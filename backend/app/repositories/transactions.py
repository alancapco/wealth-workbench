"""Transaction, audit, and idempotency repositories."""
import hashlib
import json
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AuditEvent, IdempotencyRequest


class AuditRepository:
    """Repository for append-only audit events with chain integrity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_event(
        self,
        tenant_id: str,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str,
        correlation_id: UUID,
        safe_details: dict,
        client_id: UUID | None = None,
        workflow_id: UUID | None = None,
        revision_id: UUID | None = None,
        previous_hash: str | None = None,
    ) -> AuditEvent:
        """Record append-only audit event with hash chain."""
        # Compute event hash from content
        event_content = {
            "tenant_id": tenant_id,
            "actor": actor,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "correlation_id": str(correlation_id),
            "occurred_at": datetime.now(UTC).isoformat(),
            "previous_hash": previous_hash,
            "safe_details": safe_details,
        }
        event_hash = hashlib.sha256(json.dumps(event_content, sort_keys=True).encode()).hexdigest()

        event = AuditEvent(
            tenant_id=tenant_id,
            client_id=client_id,
            workflow_id=workflow_id,
            revision_id=revision_id,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            correlation_id=correlation_id,
            occurred_at=datetime.now(UTC),
            previous_hash=previous_hash,
            event_hash=event_hash,
            safe_details=json.dumps(safe_details),
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_events_for_resource(
        self, tenant_id: str, resource_type: str, resource_id: str, limit: int = 100
    ) -> list[AuditEvent]:
        """Retrieve audit events for a specific resource."""
        stmt = (
            select(AuditEvent)
            .where(
                AuditEvent.tenant_id == tenant_id,
                AuditEvent.resource_type == resource_type,
                AuditEvent.resource_id == resource_id,
            )
            .order_by(AuditEvent.occurred_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class IdempotencyRepository:
    """Repository for idempotent request tracking."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_request(
        self,
        tenant_id: str,
        actor: str,
        method: str,
        path: str,
        idempotency_key: UUID,
        request_hash: str,
    ) -> tuple[IdempotencyRequest, bool]:
        """
        Get existing idempotency request or create new one.
        Returns (request, is_new).
        """
        stmt = select(IdempotencyRequest).where(
            IdempotencyRequest.tenant_id == tenant_id,
            IdempotencyRequest.actor == actor,
            IdempotencyRequest.method == method,
            IdempotencyRequest.path == path,
            IdempotencyRequest.idempotency_key == idempotency_key,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing, False

        # Create new request
        request = IdempotencyRequest(
            tenant_id=tenant_id,
            actor=actor,
            method=method,
            path=path,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            status="IN_PROGRESS",
            created_at=datetime.now(UTC),
        )
        self.session.add(request)
        await self.session.flush()
        return request, True

    async def complete_request(
        self,
        request: IdempotencyRequest,
        response_status: int,
        response_body: dict,
        resource_ref: str | None = None,
    ) -> None:
        """Mark idempotency request as completed."""
        request.status = "COMPLETED"
        request.response_status = response_status
        request.response_body = json.dumps(response_body)
        request.resource_ref = resource_ref
        request.completed_at = datetime.now(UTC)
        await self.session.flush()


class TransactionContext:
    """
    Helper for atomic transaction boundaries with audit and idempotency.
    
    Ensures that business writes, audit events, and idempotency tracking
    are committed together or rolled back together.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit_repo = AuditRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)

    async def record_audit(
        self,
        tenant_id: str,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str,
        correlation_id: UUID,
        safe_details: dict,
        **kwargs,
    ) -> AuditEvent:
        """Record audit event within current transaction."""
        return await self.audit_repo.record_event(
            tenant_id=tenant_id,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            safe_details=safe_details,
            **kwargs,
        )

    async def commit(self) -> None:
        """Commit transaction (business + audit + idempotency)."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback entire transaction."""
        await self.session.rollback()
