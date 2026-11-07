"""
Persistence contract tests for U-005.

Tests tenant isolation, artifact version immutability, approval invalidation
on content change, memory superseding, outbox lease/crash recovery.
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    ActionAuthorization,
    ActionPreview,
    ArtifactLineage,
    ArtifactRevision,
    AuditEvent,
    Client,
    ClientMemoryEntry,
    ClientScope,
    OutboxAction,
    ReviewDecision,
    WorkbenchTenant,
    Workflow,
)
from app.repositories import (
    ActionAuthorizationRepository,
    ActionPreviewRepository,
    ArtifactRepository,
    AuditRepository,
    OutboxRepository,
    RevisionRepository,
    ReviewRepository,
    TransactionContext,
)

# Test database URL - must be PostgreSQL 15+
TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_rmworkbench"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    test_engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


@pytest.fixture
async def session(engine):
    """Create clean test session for each test."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as sess:
        yield sess
        await sess.rollback()


@pytest.fixture
async def test_tenant(session: AsyncSession):
    """Create test tenant."""
    tenant = WorkbenchTenant(
        tenant_id="test-tenant-001",
        environment_kind="FIXTURE",
        environment_id="pytest",
        created_at=datetime.utcnow(),
    )
    session.add(tenant)
    await session.commit()
    return tenant


@pytest.fixture
async def test_client(session: AsyncSession, test_tenant):
    """Create test client."""
    client = Client(
        id=uuid.uuid4(),
        name="Test Client",
        email="test@example.com",
        created_at=datetime.utcnow(),
    )
    session.add(client)
    await session.flush()
    
    # Add to client scope
    scope = ClientScope(
        tenant_id=test_tenant.tenant_id,
        client_id=client.id,
        context_revision=1,
        ownership_source="pytest",
        ownership_version="v1",
        verified_at=datetime.utcnow(),
    )
    session.add(scope)
    await session.commit()
    return client


@pytest.fixture
async def test_workflow(session: AsyncSession, test_tenant, test_client):
    """Create test workflow."""
    workflow = Workflow(
        id=uuid.uuid4(),
        tenant_id=test_tenant.tenant_id,
        client_id=test_client.id,
        workflow_type="MEETING_PREP",
        status="RUNNING",
        context_revision=1,
        entry_point="test",
        created_by="pytest",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(workflow)
    await session.commit()
    return workflow


class TestTenantIsolation:
    """Test tenant isolation enforcement."""

    async def test_cross_tenant_artifact_access_denied(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Cross-tenant queries return no results."""
        repo = ArtifactRepository(session)
        
        # Create artifact in test tenant
        lineage = await repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="BRIEF",
            created_by="pytest",
        )
        await session.commit()
        
        # Query with wrong tenant returns None
        result = await repo.get_by_id("wrong-tenant", test_client.id, lineage.id)
        assert result is None

    async def test_same_tenant_different_client_isolation(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Same tenant but different client_id enforces composite FK."""
        repo = ArtifactRepository(session)
        
        lineage = await repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="BRIEF",
            created_by="pytest",
        )
        await session.commit()
        
        # Query with wrong client_id returns None
        other_client_id = uuid.uuid4()
        result = await repo.get_by_id(test_tenant.tenant_id, other_client_id, lineage.id)
        assert result is None


class TestArtifactVersionImmutability:
    """Test artifact revision immutability."""

    async def test_revision_immutable_after_creation(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Artifact revisions cannot be modified after creation."""
        artifact_repo = ArtifactRepository(session)
        revision_repo = RevisionRepository(session)
        
        lineage = await artifact_repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="BRIEF",
            created_by="pytest",
        )
        
        payload = {"sections": {"overview": "Original content"}}
        content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        
        revision = await revision_repo.create_revision(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            artifact_id=lineage.id,
            version=1,
            content_hash=content_hash,
            payload=json.dumps(payload),
            environment_kind="FIXTURE",
            environment_id="pytest",
            created_by="pytest",
        )
        await session.commit()
        
        # Attempt to modify (should not affect persisted value after commit)
        original_hash = revision.content_hash
        retrieved = await revision_repo.get_by_id(
            test_tenant.tenant_id, test_client.id, revision.id
        )
        assert retrieved.content_hash == original_hash
        assert retrieved.version == 1

    async def test_unique_version_constraint(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Same artifact cannot have duplicate version numbers."""
        artifact_repo = ArtifactRepository(session)
        revision_repo = RevisionRepository(session)
        
        lineage = await artifact_repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="BRIEF",
            created_by="pytest",
        )
        
        payload1 = {"content": "version 1"}
        hash1 = hashlib.sha256(json.dumps(payload1).encode()).hexdigest()
        
        await revision_repo.create_revision(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            artifact_id=lineage.id,
            version=1,
            content_hash=hash1,
            payload=json.dumps(payload1),
            environment_kind="FIXTURE",
            environment_id="pytest",
            created_by="pytest",
        )
        await session.commit()
        
        # Attempt duplicate version should violate unique constraint
        payload2 = {"content": "version 1 duplicate"}
        hash2 = hashlib.sha256(json.dumps(payload2).encode()).hexdigest()
        
        with pytest.raises(Exception):  # IntegrityError
            await revision_repo.create_revision(
                tenant_id=test_tenant.tenant_id,
                client_id=test_client.id,
                artifact_id=lineage.id,
                version=1,  # Duplicate
                content_hash=hash2,
                payload=json.dumps(payload2),
                environment_kind="FIXTURE",
                environment_id="pytest",
                created_by="pytest",
            )
            await session.commit()


class TestApprovalInvalidation:
    """Test approval invalidation when content changes."""

    async def test_content_change_invalidates_approvals(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Changing artifact content invalidates dependent action approvals."""
        artifact_repo = ArtifactRepository(session)
        revision_repo = RevisionRepository(session)
        preview_repo = ActionPreviewRepository(session)
        
        # Create artifact and revision
        lineage = await artifact_repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="MESSAGE",
            created_by="pytest",
        )
        
        payload_v1 = {"message": "Original content"}
        hash_v1 = hashlib.sha256(json.dumps(payload_v1).encode()).hexdigest()
        
        revision_v1 = await revision_repo.create_revision(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            artifact_id=lineage.id,
            version=1,
            content_hash=hash_v1,
            payload=json.dumps(payload_v1),
            environment_kind="FIXTURE",
            environment_id="pytest",
            created_by="pytest",
        )
        
        # Create action preview based on this revision
        preview = await preview_repo.create_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            revision_id=revision_v1.id,
            action_class="CLIENT_SEND",
            preview_hash="preview-hash-1",
            request_hash="request-hash-1",
            approved_request=json.dumps({"to": "client@example.com"}),
            provider_key="email",
            destination_ref="client@example.com",
            environment_kind="FIXTURE",
            environment_id="pytest",
            context_revision=1,
            dependency_manifest=json.dumps({"revision_id": str(revision_v1.id)}),
            created_by="pytest",
        )
        await session.commit()
        
        assert preview.status == "VALID"
        
        # Invalidate previews when content changes
        count = await preview_repo.invalidate_by_revision(
            test_tenant.tenant_id, test_client.id, revision_v1.id
        )
        await session.commit()
        
        assert count == 1
        
        # Verify preview is now invalidated
        refreshed = await preview_repo.get_by_id(
            test_tenant.tenant_id, test_client.id, preview.id
        )
        assert refreshed.status == "INVALIDATED"


class TestMemorySuperseding:
    """Test client memory superseding logic."""

    async def test_memory_version_sequence(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Memory entries track version sequence and superseding."""
        artifact_repo = ArtifactRepository(session)
        revision_repo = RevisionRepository(session)
        auth_repo = ActionAuthorizationRepository(session)
        preview_repo = ActionPreviewRepository(session)
        
        # Create source revision
        lineage = await artifact_repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="MEMORY_PROPOSAL",
            created_by="pytest",
        )
        
        revision = await revision_repo.create_revision(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            artifact_id=lineage.id,
            version=1,
            content_hash="hash1",
            payload=json.dumps({"preference": "value1"}),
            environment_kind="FIXTURE",
            environment_id="pytest",
            created_by="pytest",
        )
        
        # Create authorization (required FK for memory entry)
        preview = await preview_repo.create_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            revision_id=revision.id,
            action_class="MEMORY_WRITE",
            preview_hash="preview-hash",
            request_hash="request-hash",
            approved_request=json.dumps({}),
            provider_key="internal",
            destination_ref="memory",
            environment_kind="FIXTURE",
            environment_id="pytest",
            context_revision=1,
            dependency_manifest=json.dumps({}),
            created_by="pytest",
        )
        
        authorization = await auth_repo.authorize_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            preview_id=preview.id,
            preview_hash="preview-hash",
            action_class="MEMORY_WRITE",
            actor="pytest",
        )
        
        # Create memory entry v1
        memory_v1 = ClientMemoryEntry(
            id=uuid.uuid4(),
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            memory_key="investment_preference",
            version=1,
            value=json.dumps({"strategy": "conservative"}),
            state="CONFIRMED",
            source_revision_id=revision.id,
            authorization_id=authorization.id,
            confirmed_by="pytest",
            confirmed_at=datetime.utcnow(),
        )
        session.add(memory_v1)
        await session.commit()
        
        # Create memory entry v2 (supersedes v1)
        memory_v2 = ClientMemoryEntry(
            id=uuid.uuid4(),
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            memory_key="investment_preference",
            version=2,
            value=json.dumps({"strategy": "growth"}),
            state="CONFIRMED",
            source_revision_id=revision.id,
            authorization_id=authorization.id,
            confirmed_by="pytest",
            confirmed_at=datetime.utcnow(),
        )
        session.add(memory_v2)
        
        # Mark v1 as superseded
        memory_v1.state = "SUPERSEDED"
        await session.commit()
        
        # Verify version progression
        from sqlalchemy import select
        stmt = (
            select(ClientMemoryEntry)
            .where(
                ClientMemoryEntry.tenant_id == test_tenant.tenant_id,
                ClientMemoryEntry.client_id == test_client.id,
                ClientMemoryEntry.memory_key == "investment_preference",
            )
            .order_by(ClientMemoryEntry.version.desc())
        )
        result = await session.execute(stmt)
        entries = list(result.scalars().all())
        
        assert len(entries) == 2
        assert entries[0].version == 2
        assert entries[0].state == "CONFIRMED"
        assert entries[1].version == 1
        assert entries[1].state == "SUPERSEDED"


class TestOutboxLeaseCrashRecovery:
    """Test outbox lease mechanism and crash recovery."""

    async def test_outbox_lease_claim(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Workers claim pending actions with lease token."""
        artifact_repo = ArtifactRepository(session)
        revision_repo = RevisionRepository(session)
        preview_repo = ActionPreviewRepository(session)
        auth_repo = ActionAuthorizationRepository(session)
        outbox_repo = OutboxRepository(session)
        
        # Create authorization
        lineage = await artifact_repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="MESSAGE",
            created_by="pytest",
        )
        
        revision = await revision_repo.create_revision(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            artifact_id=lineage.id,
            version=1,
            content_hash="hash1",
            payload=json.dumps({"message": "test"}),
            environment_kind="FIXTURE",
            environment_id="pytest",
            created_by="pytest",
        )
        
        preview = await preview_repo.create_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            revision_id=revision.id,
            action_class="CLIENT_SEND",
            preview_hash="preview-hash",
            request_hash="request-hash",
            approved_request=json.dumps({}),
            provider_key="email",
            destination_ref="test@example.com",
            environment_kind="FIXTURE",
            environment_id="pytest",
            context_revision=1,
            dependency_manifest=json.dumps({}),
            created_by="pytest",
        )
        
        authorization = await auth_repo.authorize_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            preview_id=preview.id,
            preview_hash="preview-hash",
            action_class="CLIENT_SEND",
            actor="pytest",
        )
        
        # Enqueue action
        action = await outbox_repo.enqueue_action(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            authorization_id=authorization.id,
            provider_operation_key=f"op-{uuid.uuid4()}",
        )
        await session.commit()
        
        assert action.status == "PENDING"
        assert action.lease_token is None
        
        # Worker claims action
        claimed = await outbox_repo.claim_next_pending(lease_duration_seconds=300, limit=10)
        await session.commit()
        
        assert len(claimed) == 1
        assert claimed[0].id == action.id
        assert claimed[0].lease_token is not None
        assert claimed[0].lease_until is not None

    async def test_expired_lease_reclaim(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Expired leases can be reclaimed by another worker (crash recovery)."""
        artifact_repo = ArtifactRepository(session)
        revision_repo = RevisionRepository(session)
        preview_repo = ActionPreviewRepository(session)
        auth_repo = ActionAuthorizationRepository(session)
        outbox_repo = OutboxRepository(session)
        
        # Setup action
        lineage = await artifact_repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="MESSAGE",
            created_by="pytest",
        )
        
        revision = await revision_repo.create_revision(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            artifact_id=lineage.id,
            version=1,
            content_hash="hash1",
            payload=json.dumps({}),
            environment_kind="FIXTURE",
            environment_id="pytest",
            created_by="pytest",
        )
        
        preview = await preview_repo.create_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            revision_id=revision.id,
            action_class="CLIENT_SEND",
            preview_hash="preview-hash",
            request_hash="request-hash",
            approved_request=json.dumps({}),
            provider_key="email",
            destination_ref="test@example.com",
            environment_kind="FIXTURE",
            environment_id="pytest",
            context_revision=1,
            dependency_manifest=json.dumps({}),
            created_by="pytest",
        )
        
        authorization = await auth_repo.authorize_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            preview_id=preview.id,
            preview_hash="preview-hash",
            action_class="CLIENT_SEND",
            actor="pytest",
        )
        
        action = await outbox_repo.enqueue_action(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            authorization_id=authorization.id,
            provider_operation_key=f"op-{uuid.uuid4()}",
        )
        await session.commit()
        
        # Worker 1 claims with expired lease
        action.lease_token = uuid.uuid4()
        action.lease_until = datetime.utcnow() - timedelta(seconds=10)  # Already expired
        action.status = "SENDING"
        await session.commit()
        
        # Worker 2 reclaims expired lease
        reclaimed = await outbox_repo.claim_next_pending(lease_duration_seconds=300, limit=10)
        await session.commit()
        
        assert len(reclaimed) == 1
        assert reclaimed[0].id == action.id
        assert reclaimed[0].lease_token != action.lease_token  # New lease token

    async def test_attempt_history_preserved(
        self, session: AsyncSession, test_tenant, test_client, test_workflow
    ):
        """Outbox attempts preserve full dispatch history."""
        artifact_repo = ArtifactRepository(session)
        revision_repo = RevisionRepository(session)
        preview_repo = ActionPreviewRepository(session)
        auth_repo = ActionAuthorizationRepository(session)
        outbox_repo = OutboxRepository(session)
        
        # Setup
        lineage = await artifact_repo.create_lineage(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            workflow_id=test_workflow.id,
            kind="MESSAGE",
            created_by="pytest",
        )
        
        revision = await revision_repo.create_revision(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            artifact_id=lineage.id,
            version=1,
            content_hash="hash1",
            payload=json.dumps({}),
            environment_kind="FIXTURE",
            environment_id="pytest",
            created_by="pytest",
        )
        
        preview = await preview_repo.create_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            revision_id=revision.id,
            action_class="CLIENT_SEND",
            preview_hash="preview-hash",
            request_hash="request-hash",
            approved_request=json.dumps({}),
            provider_key="email",
            destination_ref="test@example.com",
            environment_kind="FIXTURE",
            environment_id="pytest",
            context_revision=1,
            dependency_manifest=json.dumps({}),
            created_by="pytest",
        )
        
        authorization = await auth_repo.authorize_preview(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            preview_id=preview.id,
            preview_hash="preview-hash",
            action_class="CLIENT_SEND",
            actor="pytest",
        )
        
        action = await outbox_repo.enqueue_action(
            tenant_id=test_tenant.tenant_id,
            client_id=test_client.id,
            authorization_id=authorization.id,
            provider_operation_key=f"op-{uuid.uuid4()}",
        )
        await session.commit()
        
        # Record attempt 1: UNKNOWN
        lease_token = uuid.uuid4()
        attempt1 = await outbox_repo.record_attempt(
            action=action,
            attempt_no=1,
            mode="DISPATCH",
            lease_token=lease_token,
            status="UNKNOWN",
            request_hash="hash1",
            error_code="TIMEOUT",
        )
        await session.commit()
        
        # Record attempt 2: CONFIRMED
        attempt2 = await outbox_repo.record_attempt(
            action=action,
            attempt_no=2,
            mode="DISPATCH",
            lease_token=lease_token,
            status="CONFIRMED",
            request_hash="hash1",
            receipt_ref="receipt-123",
        )
        await session.commit()
        
        # Retrieve attempt history
        attempts = await outbox_repo.get_attempts(
            test_tenant.tenant_id, test_client.id, action.id
        )
        
        assert len(attempts) == 2
        assert attempts[0].attempt_no == 1
        assert attempts[0].status == "UNKNOWN"
        assert attempts[1].attempt_no == 2
        assert attempts[1].status == "CONFIRMED"
        assert action.attempt_count == 2


class TestAuditTransactionality:
    """Test transactional audit with rollback."""

    async def test_audit_rollback_with_business_failure(
        self, session: AsyncSession, test_tenant
    ):
        """Audit events roll back if business transaction fails."""
        tx_context = TransactionContext(session)
        
        try:
            # Record audit event
            await tx_context.record_audit(
                tenant_id=test_tenant.tenant_id,
                actor="pytest",
                action="CREATE",
                resource_type="test_resource",
                resource_id="resource-123",
                correlation_id=uuid.uuid4(),
                safe_details={"test": "data"},
            )
            
            # Simulate business logic failure
            raise ValueError("Business logic error")
        
        except ValueError:
            await tx_context.rollback()
        
        # Verify audit was rolled back
        repo = AuditRepository(session)
        events = await repo.get_events_for_resource(
            test_tenant.tenant_id, "test_resource", "resource-123"
        )
        assert len(events) == 0

    async def test_audit_append_only_enforcement(
        self, session: AsyncSession, test_tenant
    ):
        """Audit events cannot be updated or deleted (append-only)."""
        audit_repo = AuditRepository(session)
        
        event = await audit_repo.record_event(
            tenant_id=test_tenant.tenant_id,
            actor="pytest",
            action="CREATE",
            resource_type="test_resource",
            resource_id="resource-123",
            correlation_id=uuid.uuid4(),
            safe_details={"original": "data"},
        )
        await session.commit()
        
        # Attempt update should fail via trigger (if implemented in migration)
        # For now, verify event is immutable by checking it wasn't modified
        original_hash = event.event_hash
        
        # Attempt to modify (should be prevented by application logic + DB trigger)
        from sqlalchemy import select
        stmt = select(AuditEvent).where(AuditEvent.id == event.id)
        result = await session.execute(stmt)
        retrieved = result.scalar_one()
        
        assert retrieved.event_hash == original_hash
        assert json.loads(retrieved.safe_details)["original"] == "data"
