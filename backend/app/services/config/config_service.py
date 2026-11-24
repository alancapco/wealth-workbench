"""Configuration service for decision gates and provider configs."""
import json
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import CapabilityControl, ConfigScope, ConfigurationRevision
from app.schemas.common import Scope


class ConfigService:
    """Service for reading configuration and capability controls (decision gates)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_gate_state(self, scope: Scope, key: str) -> tuple[bool, Optional[datetime]]:
        """Return (enabled, last_changed_at). Fail-closed when no control exists.

        ``updated_at`` used to be filled with ``now()`` by the endpoint, which made
        a never-configured gate look like it had just been changed.
        """
        control = await self._latest_control(scope, key)
        if not control:
            return False, None
        # ``enabled`` is stored as text 'true'/'false'.
        return control.enabled == "true", control.changed_at

    async def get_decision_gate(self, scope: Scope, key: str) -> bool:
        """Get decision gate status. Returns False (fail-closed) if not configured."""
        enabled, _ = await self.get_gate_state(scope, key)
        return enabled

    async def set_decision_gate(
        self,
        scope: Scope,
        key: str,
        enabled: bool,
        actor: str,
        reason: str = "Updated via Workbench UI",
    ) -> tuple[bool, datetime]:
        """Persist a new capability-control revision for a gate.

        The PATCH endpoint previously echoed the requested value without writing
        anything, so the UI reported success while the gate never changed.
        Revisions are append-only: readers take the highest revision.
        """
        scope_id = await self._ensure_scope(scope)

        max_revision = await self.session.scalar(
            select(func.coalesce(func.max(CapabilityControl.revision), 0)).where(
                CapabilityControl.tenant_id == scope.tenant_id,
                CapabilityControl.scope_id == scope_id,
                CapabilityControl.capability_key == key,
            )
        )

        # The physical column is TIMESTAMPTZ. Pass an aware UTC value; a naive
        # datetime would be interpreted in the client's local zone (UTC+8 here)
        # and would read back eight hours in the past.
        changed_at = datetime.now(UTC)
        control = CapabilityControl(
            id=uuid4(),
            tenant_id=scope.tenant_id,
            scope_id=scope_id,
            capability_key=key,
            enabled="true" if enabled else "false",
            revision=int(max_revision or 0) + 1,
            cohort_refs="[]",
            reason=reason,
            actor=actor,
            changed_at=changed_at,
        )
        self.session.add(control)
        await self.session.flush()
        return enabled, changed_at

    async def _latest_control(self, scope: Scope, key: str) -> Optional[CapabilityControl]:
        scope_id = await self._get_scope_id(scope)
        if not scope_id:
            return None
        stmt = (
            select(CapabilityControl)
            .where(
                CapabilityControl.tenant_id == scope.tenant_id,
                CapabilityControl.scope_id == scope_id,
                CapabilityControl.capability_key == key,
            )
            .order_by(CapabilityControl.revision.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _ensure_scope(self, scope: Scope) -> UUID:
        """Create the ConfigScope row for a scope on first write."""
        existing = await self._get_scope_id(scope)
        if existing:
            return existing
        scope_id = uuid4()
        self.session.add(
            ConfigScope(
                id=scope_id,
                tenant_id=scope.tenant_id,
                book_id=scope.book_id,
                jurisdiction=scope.jurisdiction,
                scope_key=json.dumps([scope.tenant_id, scope.book_id, scope.jurisdiction]),
            )
        )
        await self.session.flush()
        return scope_id

    async def list_active_configs(self, scope: Scope) -> list[ConfigurationRevision]:
        """List active configurations for a scope."""
        scope_id = await self._get_scope_id(scope)
        if not scope_id:
            return []

        stmt = (
            select(ConfigurationRevision)
            .where(
                ConfigurationRevision.tenant_id == scope.tenant_id,
                ConfigurationRevision.scope_id == scope_id,
                ConfigurationRevision.status.in_(["APPROVED", "VALIDATED"]),
            )
            .order_by(ConfigurationRevision.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_provider_config(self, scope: Scope, provider_type: str) -> Optional[dict]:
        """
        Get provider integration configuration. Returns None if UNCONFIGURED.
        
        Provider configs are stored as INTEGRATION class configurations.
        """
        scope_id = await self._get_scope_id(scope)
        if not scope_id:
            return None

        stmt = (
            select(ConfigurationRevision)
            .where(
                ConfigurationRevision.tenant_id == scope.tenant_id,
                ConfigurationRevision.scope_id == scope_id,
                ConfigurationRevision.config_class == "INTEGRATION",
                ConfigurationRevision.config_key == f"provider.{provider_type}",
                ConfigurationRevision.status == "APPROVED",
            )
            .order_by(ConfigurationRevision.revision.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return None  # UNCONFIGURED

        # Parse value (stored as JSONB text)
        return json.loads(config.value)

    async def _get_scope_id(self, scope: Scope) -> Optional[UUID]:
        """Resolve scope to scope_id."""
        # Build scope_key per architecture: [tenant_id, book_id, jurisdiction]
        scope_key = json.dumps([scope.tenant_id, scope.book_id, scope.jurisdiction])

        stmt = select(ConfigScope.id).where(
            ConfigScope.tenant_id == scope.tenant_id,
            ConfigScope.scope_key == scope_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
