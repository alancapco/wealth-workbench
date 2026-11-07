"""Audit service for recording and querying audit events."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AuditEvent
from app.repositories.transactions import AuditRepository


class AuditService:
    """Service for audit event recording and querying."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit_repo = AuditRepository(session)

    async def record_audit_event(
        self,
        tenant_id: str,
        principal: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict,
        correlation_id: UUID,
        client_id: Optional[UUID] = None,
        workflow_id: Optional[UUID] = None,
        revision_id: Optional[UUID] = None,
    ) -> AuditEvent:
        """
        Record an audit event for critical operations.
        
        Auto-record for:
        - workflow start, pause, abandon
        - artifact approval/rejection
        - action execution
        - config change
        - consent withdrawal
        """
        return await self.audit_repo.record_event(
            tenant_id=tenant_id,
            actor=principal,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            safe_details=details,
            client_id=client_id,
            workflow_id=workflow_id,
            revision_id=revision_id,
        )

    async def query_audit_log(
        self,
        tenant_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """
        Query audit log with filters (tenant-scoped).
        
        Always tenant-scoped for security isolation.
        """
        query = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id)

        if resource_type:
            query = query.where(AuditEvent.resource_type == resource_type)
        if resource_id:
            query = query.where(AuditEvent.resource_id == resource_id)
        if action:
            query = query.where(AuditEvent.action == action)
        if from_time:
            query = query.where(AuditEvent.occurred_at >= from_time)
        if to_time:
            query = query.where(AuditEvent.occurred_at <= to_time)

        query = query.order_by(AuditEvent.occurred_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
