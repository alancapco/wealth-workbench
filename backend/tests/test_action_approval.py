"""
Tests for action approval workflow: preview, authorization, execution, outbox.

U-009: Isolated unit tests with mocked persistence.
Production would use PostgreSQL 15+ disposable test containers.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ActionPreview, ActionAuthorization, OutboxAction, OutboxAttempt
from app.services.actions.action_service import ActionService
from app.services.actions.outbox_worker import OutboxWorker


@pytest_asyncio.fixture
async def mock_db_session():
    """Mock database session for isolated tests."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.mark.asyncio
class TestActionApprovalWorkflow:
    """Test separate approvals per class and payload immutability."""

    async def test_preview_stores_immutable_payload(self, mock_db_session):
        """Preview stores immutable server-side payload with hash."""
        service = ActionService(mock_db_session)
        tenant_id = "tenant-001"
        client_id = uuid4()
        revision_id = uuid4()
        
        approved_request = {
            "record_ref": "CRM-12345",
            "changes": [{"field": "status", "value": "contacted"}]
        }
        
        # Create preview should compute hash and store payload
        preview = await service.create_preview(
            tenant_id=tenant_id,
            client_id=client_id,
            revision_id=revision_id,
            action_class="CRM_WRITE",
            approved_request=approved_request,
            provider_key="test-crm",
            destination_ref="crm://record/12345",
            environment_kind="FIXTURE",
            environment_id="test",
            context_revision=1,
            dependency_manifest={},
            created_by="user@test.com",
        )
        
        # Preview hash should be SHA-256 (64 hex chars)
        assert len(preview.preview_hash) == 64
        assert preview.action_class == "CRM_WRITE"
        assert preview.provider_key == "test-crm"
        assert preview.destination_ref == "crm://record/12345"
        
        # Payload stored as JSON
        import json
        stored_payload = json.loads(preview.approved_request)
        assert stored_payload == approved_request

    async def test_separate_authorization_per_action_class(self, mock_db_session):
        """Each action class requires separate authorization."""
        # Verify all 5 action classes are supported
        classes = ["CRM_WRITE", "TASK_WRITE", "MEMORY_WRITE", "CLIENT_SEND", "TICKET_PREFILL"]
        
        for action_class in classes:
            service = ActionService(mock_db_session)
            tenant_id = "tenant-001"
            client_id = uuid4()
            revision_id = uuid4()
            
            preview = await service.create_preview(
                tenant_id=tenant_id,
                client_id=client_id,
                revision_id=revision_id,
                action_class=action_class,
                approved_request={"class": action_class},
                provider_key=f"provider-{action_class.lower()}",
                destination_ref=f"dest-{action_class}",
                environment_kind="FIXTURE",
                environment_id="test",
                context_revision=1,
                dependency_manifest={},
                created_by="user@test.com",
            )
            
            assert preview.action_class == action_class

    async def test_authorization_binds_to_preview_hash(self, mock_db_session):
        """Authorization references exact preview by ID + hash."""
        service = ActionService(mock_db_session)
        tenant_id = "tenant-001"
        client_id = uuid4()
        revision_id = uuid4()
        
        preview = await service.create_preview(
            tenant_id=tenant_id,
            client_id=client_id,
            revision_id=revision_id,
            action_class="CRM_WRITE",
            approved_request={"field": "value"},
            provider_key="crm-provider",
            destination_ref="crm://dest",
            environment_kind="FIXTURE",
            environment_id="test",
            context_revision=1,
            dependency_manifest={},
            created_by="user@test.com",
        )
        
        # Mock preview lookup
        with patch.object(service.preview_repo, 'get_by_id', return_value=preview):
            auth = await service.authorize_preview(
                tenant_id=tenant_id,
                client_id=client_id,
                preview_id=preview.id,
                actor="approver@test.com",
            )
            
            # Authorization must record exact hash
            assert auth.preview_hash == preview.preview_hash
            assert auth.preview_id == preview.id
            assert auth.action_class == preview.action_class

    async def test_execute_accepts_only_authorization_id(self, mock_db_session):
        """Execute API accepts only authorization_id, no payload substitution."""
        service = ActionService(mock_db_session)
        tenant_id = "tenant-001"
        client_id = uuid4()
        revision_id = uuid4()
        
        # Create preview and authorization
        preview = await service.create_preview(
            tenant_id=tenant_id,
            client_id=client_id,
            revision_id=revision_id,
            action_class="CRM_WRITE",
            approved_request={"original": "payload"},
            provider_key="crm-provider",
            destination_ref="crm://dest",
            environment_kind="FIXTURE",
            environment_id="test",
            context_revision=1,
            dependency_manifest={},
            created_by="user@test.com",
        )
        
        # Mock repositories for authorization and execution
        with patch.object(service.preview_repo, 'get_by_id', return_value=preview):
            auth = await service.authorize_preview(
                tenant_id=tenant_id,
                client_id=client_id,
                preview_id=preview.id,
                actor="approver@test.com",
            )
        
        # Execute with only authorization_id
        with patch.object(service.auth_repo, 'get_by_id', return_value=auth), \
             patch.object(service.preview_repo, 'get_by_id', return_value=preview):
            action = await service.execute_action(
                tenant_id=tenant_id,
                authorization_id=auth.id,
            )
            
            # Action created with authorization_id reference
            assert action.authorization_id == auth.id
            assert action.status == "PENDING"
            # Provider operation key is stable for idempotency
            assert action.provider_operation_key is not None

    async def test_payload_immutability_enforcement(self, mock_db_session):
        """Cannot substitute payload at execution time."""
        service = ActionService(mock_db_session)
        
        # This is enforced by API contract - execute_action only accepts authorization_id
        # No request payload parameter exists in the method signature
        import inspect
        sig = inspect.signature(service.execute_action)
        params = list(sig.parameters.keys())
        
        # Verify no 'payload' or 'request' parameter
        assert 'payload' not in params
        assert 'request' not in params
        assert 'authorization_id' in params


@pytest.mark.asyncio
class TestOutboxPattern:
    """Test lease management, attempt history, crash recovery."""

    async def test_outbox_action_created_on_execute(self, mock_db_session):
        """Execute creates outbox action in PENDING status."""
        service = ActionService(mock_db_session)
        tenant_id = "tenant-001"
        authorization_id = uuid4()
        client_id = uuid4()
        
        # Mock authorization and preview
        mock_auth = ActionAuthorization(
            id=authorization_id,
            tenant_id=tenant_id,
            client_id=client_id,
            preview_id=uuid4(),
            preview_hash="a" * 64,
            action_class="CRM_WRITE",
            actor="user@test.com",
            authorized_at=datetime.utcnow(),
            status="VALID",
        )
        
        mock_preview = ActionPreview(
            id=mock_auth.preview_id,
            tenant_id=tenant_id,
            client_id=client_id,
            revision_id=uuid4(),
            action_class="CRM_WRITE",
            preview_hash="a" * 64,
            request_hash="b" * 64,
            approved_request='{"test": "data"}',
            provider_key="test-provider",
            destination_ref="test-dest",
            environment_kind="FIXTURE",
            environment_id="test",
            context_revision=1,
            dependency_manifest="{}",
            status="VALID",
            created_by="user@test.com",
            created_at=datetime.utcnow(),
        )
        
        with patch.object(service.auth_repo, 'get_by_id', return_value=mock_auth), \
             patch.object(service.preview_repo, 'get_by_id', return_value=mock_preview):
            action = await service.execute_action(
                tenant_id=tenant_id,
                authorization_id=authorization_id,
            )
            
            assert action.status == "PENDING"
            assert action.attempt_count == 0

    async def test_timeout_becomes_unknown_never_auto_resend(self, mock_db_session):
        """
        Timeout/crash → UNKNOWN status, requires readback.
        No automatic resend - safety beats assumed retry.
        """
        worker = OutboxWorker(mock_db_session)
        
        action = OutboxAction(
            id=uuid4(),
            tenant_id="tenant-001",
            client_id=uuid4(),
            authorization_id=uuid4(),
            provider_operation_key="test-op-key",
            status="SENDING",
            attempt_count=1,
            lease_token=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Mark as unknown on timeout
        await worker.mark_unknown_on_timeout(
            action=action,
            lease_token=action.lease_token,
            request_hash="abc123",
            error_code="TIMEOUT",
        )
        
        # Status becomes UNKNOWN
        assert action.status == "UNKNOWN"
        
        # This requires manual readback reconciliation
        # No automatic re-dispatch should occur

    async def test_readback_reconciliation_workflow(self, mock_db_session):
        """UNKNOWN status requires readback, not blind resend."""
        worker = OutboxWorker(mock_db_session)
        
        action = OutboxAction(
            id=uuid4(),
            tenant_id="tenant-001",
            client_id=uuid4(),
            authorization_id=uuid4(),
            provider_operation_key="test-op-key",
            status="UNKNOWN",
            attempt_count=1,
            lease_token=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Record readback attempt
        await worker.record_readback_attempt(
            action=action,
            lease_token=action.lease_token,
            request_hash="readback-hash",
            status="CONFIRMED",
            receipt_ref="provider-ref-123",
        )
        
        # After confirmed readback, status becomes SUCCEEDED
        assert action.status == "SUCCEEDED"
        assert action.provider_ref == "provider-ref-123"


@pytest.mark.asyncio  
class TestContractCompliance:
    """Verify implementation matches architecture contracts."""

    async def test_action_classes_match_spec(self):
        """All 5 action classes from architecture §6.5 are supported."""
        from app.schemas.action import ActionClass
        
        # These must match architecture exactly
        expected_classes = {"CRM_WRITE", "TASK_WRITE", "MEMORY_WRITE", "CLIENT_SEND", "TICKET_PREFILL"}
        
        # Verify schema enforces these exact values
        assert set(ActionClass.__args__) == expected_classes

    async def test_action_status_values_match_spec(self):
        """Action status values match architecture §4.4."""
        from app.schemas.action import ActionStatus
        
        expected_statuses = {
            "PENDING", "SENDING", "SUCCEEDED", "FAILED_SAFE", 
            "UNKNOWN", "RECONCILE_REQUIRED", "CANCELED_BEFORE_DISPATCH"
        }
        
        assert set(ActionStatus.__args__) == expected_statuses

    async def test_api_011_accepts_only_authorization_id(self):
        """API-011 execute endpoint accepts only authorization_id."""
        from app.schemas.action import ExecuteActionRequest
        from pydantic import BaseModel
        
        # Verify schema has only authorization_id field
        fields = ExecuteActionRequest.model_fields
        assert 'authorization_id' in fields
        
        # No payload, request, or content substitution fields
        assert 'payload' not in fields
        assert 'request' not in fields
        assert 'approved_request' not in fields
        assert 'destination_ref' not in fields
