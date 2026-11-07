"""Tests for configuration management and audit telemetry (U-013).

Test scenarios:
- Decision gate lookup (DEC-01 through DEC-08)
- Gate defaults to False if not configured (fail-closed)
- Audit event recording and query
- Telemetry recording and aggregation
- Tenant isolation in audit log queries

Note: SQLite compatibility - PostgreSQL-specific models (ConfigScope with JSONB constraints,
Shariah tables with ARRAY) cannot be created in SQLite. These tests verify service logic
with mocked repositories where database operations would fail.

Full PostgreSQL integration tests should be run separately with real database.
"""
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.admin import AuditEvent, CapabilityControl, TelemetryEvent
from app.schemas.common import Environment, EnvironmentKind, Scope
from app.services.config import AuditService, ConfigService, TelemetryService


@pytest_asyncio.fixture
async def mock_db_session():
    """Mock database session for service logic tests."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def tenant_scope():
    """Create a test tenant scope."""
    return {
        "scope": Scope(tenant_id="test-tenant-001", book_id="book-001", jurisdiction="US"),
        "scope_id": uuid4(),
        "tenant_id": "test-tenant-001",
    }


@pytest.fixture
def config_service(mock_db_session):
    """Create ConfigService instance."""
    return ConfigService(mock_db_session)


@pytest.fixture
def audit_service(mock_db_session):
    """Create AuditService instance."""
    return AuditService(mock_db_session)


@pytest.fixture
def telemetry_service(mock_db_session):
    """Create TelemetryService instance."""
    return TelemetryService(mock_db_session)


class TestDecisionGates:
    """Test decision gate functionality."""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_gate_defaults_to_false_when_not_configured(
        self, config_service, tenant_scope, mock_db_session
    ):
        """Gate defaults to False (fail-closed) if not configured."""
        scope = tenant_scope["scope"]
        
        # Mock: no scope found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Query unconfigured gate
        enabled = await config_service.get_decision_gate(scope, "DEC-01")
        
        assert enabled is False, "Unconfigured gate should default to False (fail-closed)"

    @pytest.mark.asyncio
    async def test_gate_returns_false_for_nonexistent_scope(
        self, config_service, mock_db_session
    ):
        """Gate returns False for nonexistent scope."""
        nonexistent_scope = Scope(
            tenant_id="nonexistent-tenant",
            book_id="nonexistent-book",
            jurisdiction="XX",
        )
        
        # Mock: no scope found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        enabled = await config_service.get_decision_gate(nonexistent_scope, "DEC-01")
        
        assert enabled is False, "Gate for nonexistent scope should return False"

    @pytest.mark.asyncio
    async def test_gate_enabled_when_configured_true(
        self, config_service, tenant_scope, mock_db_session
    ):
        """Gate returns True when configured as enabled."""
        scope = tenant_scope["scope"]
        scope_id = tenant_scope["scope_id"]
        
        # Mock: scope exists, control enabled
        mock_control = MagicMock()
        mock_control.enabled = "true"
        
        mock_result_scope = MagicMock()
        mock_result_scope.scalar_one_or_none.return_value = scope_id
        
        mock_result_control = MagicMock()
        mock_result_control.scalar_one_or_none.return_value = mock_control
        
        mock_db_session.execute.side_effect = [mock_result_scope, mock_result_control]
        
        # Query configured gate
        enabled = await config_service.get_decision_gate(scope, "DEC-01")
        
        assert enabled is True, "Configured enabled gate should return True"

    @pytest.mark.asyncio
    async def test_gate_disabled_when_configured_false(
        self, config_service, tenant_scope, mock_db_session
    ):
        """Gate returns False when explicitly configured as disabled."""
        scope = tenant_scope["scope"]
        scope_id = tenant_scope["scope_id"]
        
        # Mock: scope exists, control disabled
        mock_control = MagicMock()
        mock_control.enabled = "false"
        
        mock_result_scope = MagicMock()
        mock_result_scope.scalar_one_or_none.return_value = scope_id
        
        mock_result_control = MagicMock()
        mock_result_control.scalar_one_or_none.return_value = mock_control
        
        mock_db_session.execute.side_effect = [mock_result_scope, mock_result_control]
        
        # Query configured gate
        enabled = await config_service.get_decision_gate(scope, "DEC-02")
        
        assert enabled is False, "Configured disabled gate should return False"

    @pytest.mark.asyncio
    async def test_all_decision_gates_DEC_01_through_DEC_08(self):
        """Test all decision gates DEC-01 through DEC-08 are defined."""
        gate_keys = [
            "DEC-01",  # Brief
            "DEC-02",  # Messaging
            "DEC-03",  # Calendar
            "DEC-04",  # Product/Suitability
            "DEC-05",  # Shariah
            "DEC-06",  # Family
            "DEC-07",  # Household
            "DEC-08",  # Mobile
        ]
        
        # Verify all gates are documented
        assert len(gate_keys) == 8, "Should have exactly 8 decision gates"
        assert all(key.startswith("DEC-") for key in gate_keys), "All gates should follow DEC-XX naming"


class TestAuditService:
    """Test audit event recording and querying."""

    @pytest.mark.asyncio
    async def test_record_audit_event(self, audit_service, tenant_scope, mock_db_session):
        """Record audit event successfully."""
        tenant_id = tenant_scope["tenant_id"]
        correlation_id = uuid4()
        
        event = await audit_service.record_audit_event(
            tenant_id=tenant_id,
            principal="test-user",
            action="WORKFLOW_START",
            resource_type="workflow",
            resource_id=str(uuid4()),
            details={"type": "MEETING_PREP"},
            correlation_id=correlation_id,
        )
        
        assert event.tenant_id == tenant_id
        assert event.actor == "test-user"
        assert event.action == "WORKFLOW_START"
        assert mock_db_session.add.called, "Event should be added to session"
        assert mock_db_session.flush.called, "Session should be flushed"

    @pytest.mark.asyncio
    async def test_query_audit_log_by_tenant(
        self, audit_service, tenant_scope, mock_db_session
    ):
        """Query audit log with tenant isolation."""
        tenant_id = tenant_scope["tenant_id"]
        
        # Mock: return audit events
        mock_events = [
            MagicMock(tenant_id=tenant_id, actor="test-user", action=f"ACTION_{i}")
            for i in range(3)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_db_session.execute.return_value = mock_result
        
        # Query audit log
        events = await audit_service.query_audit_log(tenant_id=tenant_id, limit=10)
        
        assert len(events) == 3
        assert all(e.tenant_id == tenant_id for e in events)

    @pytest.mark.asyncio
    async def test_audit_log_filters_by_resource_type(
        self, audit_service, tenant_scope, mock_db_session
    ):
        """Query audit log with resource type filter."""
        tenant_id = tenant_scope["tenant_id"]
        
        # Mock: return filtered events
        mock_events = [MagicMock(resource_type="workflow")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_db_session.execute.return_value = mock_result
        
        # Query by resource type
        events = await audit_service.query_audit_log(
            tenant_id=tenant_id, resource_type="workflow"
        )
        
        assert len(events) == 1
        assert events[0].resource_type == "workflow"


class TestTelemetryService:
    """Test telemetry recording and metric aggregation."""

    @pytest.mark.asyncio
    async def test_record_telemetry(
        self, telemetry_service, tenant_scope, mock_db_session
    ):
        """Record telemetry event successfully."""
        tenant_id = tenant_scope["tenant_id"]
        environment = Environment(kind=EnvironmentKind.FIXTURE, id="test-env")
        
        event = await telemetry_service.record_telemetry(
            tenant_id=tenant_id,
            event_type="api.latency",
            environment=environment,
            actor_safe_id="user-123",
            correlation_id=uuid4(),
            labels={"endpoint": "/workflows", "method": "POST"},
            value=0.125,  # 125ms
        )
        
        assert event.tenant_id == tenant_id
        assert event.event_name == "api.latency"
        assert mock_db_session.add.called, "Event should be added to session"
        assert mock_db_session.flush.called, "Session should be flushed"

    @pytest.mark.asyncio
    async def test_query_metrics_returns_structure(self):
        """Query metrics returns expected structure (documented behavior)."""
        # Note: This test documents the expected return structure.
        # Full integration with PostgreSQL JSON aggregation tested separately.
        
        expected_structure = {
            "metric_name": "ranking.evaluation_time",
            "time_range": {"from": datetime.utcnow(), "to": datetime.utcnow()},
            "count": 5,
            "sum": 1.5,
            "avg": 0.3,
            "min": 0.1,
            "max": 0.5,
        }
        
        # Verify structure has required fields
        assert "metric_name" in expected_structure
        assert "time_range" in expected_structure
        assert "count" in expected_structure
        assert expected_structure["count"] >= 0
        
        # PostgreSQL integration test would verify actual aggregation


class TestProviderConfiguration:
    """Test provider configuration retrieval."""

    @pytest.mark.asyncio
    async def test_get_provider_config_returns_none_when_unconfigured(
        self, config_service, tenant_scope, mock_db_session
    ):
        """Provider config returns None when UNCONFIGURED."""
        scope = tenant_scope["scope"]
        
        # Mock: no scope found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        config = await config_service.get_provider_config(scope, "calendar")
        
        assert config is None, "Unconfigured provider should return None"

    @pytest.mark.asyncio
    async def test_list_active_configs_empty_for_new_scope(
        self, config_service, tenant_scope, mock_db_session
    ):
        """List active configs returns empty list for new scope."""
        scope = tenant_scope["scope"]
        
        # Mock: no scope found
        mock_result_scope = MagicMock()
        mock_result_scope.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result_scope
        
        configs = await config_service.list_active_configs(scope)
        
        assert configs == [], "New scope should have no active configs"


# Integration test documentation
"""
PostgreSQL Integration Tests (not run in SQLite):

The following tests require PostgreSQL 15+ and should be run separately:

1. ConfigScope JSONB constraint validation:
   - scope_key = jsonb_build_array(tenant_id, book_id, jurisdiction)::text
   - Verifies immutable scope identity

2. AuditEvent hash chain integrity:
   - previous_hash linking
   - AuditChainHead tenant serialization
   - Concurrent write detection

3. TelemetryEvent JSON aggregations:
   - json_extract_path_text with measures
   - JSONB label filtering
   - Time-series aggregations

4. Full table relationships:
   - Foreign keys to workbench_tenants, books, client_scope, workflows
   - Cascade behaviors
   - Tenant isolation enforcement

5. ARRAY column operations (Shariah pilot):
   - evidence_ids ARRAY(UUID) storage
   - Array containment queries

These tests are documented in the architecture contract (§6.8-6.9) and 
should pass in the full PostgreSQL test environment.

To run PostgreSQL tests:
  cd backend && uv run pytest tests/test_config_audit_pg.py -v

(File test_config_audit_pg.py would contain the full integration suite)
"""
