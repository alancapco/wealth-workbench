"""Configuration service for decision gates and provider configs."""
import json
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import CapabilityControl, ConfigScope, ConfigurationRevision
from app.schemas.common import Scope


class ConfigService:
    """Service for reading configuration and capability controls (decision gates)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_decision_gate(self, scope: Scope, key: str) -> bool:
        """
        Get decision gate status. Returns False (fail-closed) if not configured.
        
        Decision gates: DEC-01 through DEC-08 control feature availability.
        """
        # Find scope_id for the given scope
        scope_id = await self._get_scope_id(scope)
        if not scope_id:
            return False  # No scope = gate closed

        # Query capability control for this gate
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
        control = result.scalar_one_or_none()

        if not control:
            return False  # No control = gate closed (fail-closed)

        # Parse enabled field (stored as text 'true'/'false')
        return control.enabled == "true"

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
