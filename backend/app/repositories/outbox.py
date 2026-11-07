"""Outbox pattern repositories for action dispatch and lease management."""
from datetime import datetime, UTC, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ActionPreview, ActionAuthorization, OutboxAction, OutboxAttempt
from app.repositories.base import ClientScopedRepository


class ActionPreviewRepository(ClientScopedRepository[ActionPreview]):
    """Repository for action preview creation and invalidation."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ActionPreview)

    async def create_preview(
        self,
        tenant_id: str,
        client_id: UUID,
        revision_id: UUID,
        action_class: str,
        preview_hash: str,
        request_hash: str,
        approved_request: str,
        provider_key: str,
        destination_ref: str,
        environment_kind: str,
        environment_id: str,
        context_revision: int,
        dependency_manifest: str,
        created_by: str,
    ) -> ActionPreview:
        """Create action preview with exact content hash."""
        preview = ActionPreview(
            tenant_id=tenant_id,
            client_id=client_id,
            revision_id=revision_id,
            action_class=action_class,
            preview_hash=preview_hash,
            request_hash=request_hash,
            approved_request=approved_request,
            provider_key=provider_key,
            destination_ref=destination_ref,
            environment_kind=environment_kind,
            environment_id=environment_id,
            context_revision=context_revision,
            dependency_manifest=dependency_manifest,
            status="VALID",
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        self.session.add(preview)
        await self.session.flush()
        return preview

    async def invalidate_by_revision(
        self, tenant_id: str, client_id: UUID, revision_id: UUID
    ) -> int:
        """Invalidate all previews tied to a revision when content changes."""
        stmt = select(ActionPreview).where(
            ActionPreview.tenant_id == tenant_id,
            ActionPreview.client_id == client_id,
            ActionPreview.revision_id == revision_id,
            ActionPreview.status == "VALID",
        )
        result = await self.session.execute(stmt)
        previews = result.scalars().all()
        
        count = 0
        for preview in previews:
            preview.status = "INVALIDATED"
            count += 1
        
        await self.session.flush()
        return count


class ActionAuthorizationRepository(ClientScopedRepository[ActionAuthorization]):
    """Repository for action authorization tracking."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ActionAuthorization)

    async def authorize_preview(
        self,
        tenant_id: str,
        client_id: UUID,
        preview_id: UUID,
        preview_hash: str,
        action_class: str,
        actor: str,
    ) -> ActionAuthorization:
        """Create authorization binding actor to exact preview hash."""
        authorization = ActionAuthorization(
            tenant_id=tenant_id,
            client_id=client_id,
            preview_id=preview_id,
            preview_hash=preview_hash,
            action_class=action_class,
            actor=actor,
            authorized_at=datetime.now(UTC),
            status="VALID",
        )
        self.session.add(authorization)
        await self.session.flush()
        return authorization

    async def invalidate_authorization(
        self, authorization_id: UUID, invalidation_code: str
    ) -> None:
        """Invalidate authorization when dependencies change."""
        stmt = select(ActionAuthorization).where(ActionAuthorization.id == authorization_id)
        result = await self.session.execute(stmt)
        auth = result.scalar_one_or_none()
        
        if auth and auth.status == "VALID":
            auth.status = "INVALIDATED"
            auth.invalidated_at = datetime.now(UTC)
            auth.invalidation_code = invalidation_code
            await self.session.flush()


class OutboxRepository(ClientScopedRepository[OutboxAction]):
    """Repository for transactional outbox with lease-based claim and crash recovery."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, OutboxAction)

    async def enqueue_action(
        self,
        tenant_id: str,
        client_id: UUID,
        authorization_id: UUID,
        provider_operation_key: str,
    ) -> OutboxAction:
        """Enqueue action for dispatch after authorization."""
        action = OutboxAction(
            tenant_id=tenant_id,
            client_id=client_id,
            authorization_id=authorization_id,
            provider_operation_key=provider_operation_key,
            status="PENDING",
            attempt_count=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(action)
        await self.session.flush()
        return action

    async def claim_next_pending(
        self, lease_duration_seconds: int = 300, limit: int = 10
    ) -> list[OutboxAction]:
        """
        Claim pending/expired actions with lease token for worker processing.
        Returns actions that need dispatch or reconciliation.
        """
        now = datetime.now(UTC)
        lease_until = now + timedelta(seconds=lease_duration_seconds)
        lease_token = uuid4()

        # Find claimable actions: PENDING or expired lease
        stmt = (
            select(OutboxAction)
            .where(
                and_(
                    OutboxAction.status.in_(["PENDING", "SENDING", "UNKNOWN", "RECONCILE_REQUIRED"]),
                    (OutboxAction.lease_until.is_(None)) | (OutboxAction.lease_until < now),
                )
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        actions = list(result.scalars().all())

        # Assign lease
        for action in actions:
            action.lease_token = lease_token
            action.lease_until = lease_until
            action.updated_at = now

        await self.session.flush()
        return actions

    async def record_attempt(
        self,
        action: OutboxAction,
        attempt_no: int,
        mode: str,
        lease_token: UUID,
        status: str,
        request_hash: str,
        receipt_ref: str | None = None,
        error_code: str | None = None,
    ) -> OutboxAttempt:
        """Record dispatch or readback attempt."""
        attempt = OutboxAttempt(
            tenant_id=action.tenant_id,
            client_id=action.client_id,
            action_id=action.id,
            attempt_no=attempt_no,
            mode=mode,
            lease_token=lease_token,
            status=status,
            request_hash=request_hash,
            receipt_ref=receipt_ref,
            error_code=error_code,
            started_at=datetime.now(UTC),
        )
        self.session.add(attempt)
        
        # Update action attempt count and status
        action.attempt_count = attempt_no
        action.updated_at = datetime.now(UTC)
        
        if status == "CONFIRMED":
            action.submitted_at = datetime.now(UTC)
            action.status = "SENDING"
        elif status == "NOT_ACCEPTED":
            action.status = "FAILED_SAFE"
            action.last_error_code = error_code
        elif status == "UNKNOWN":
            action.status = "UNKNOWN"
            action.last_error_code = error_code

        await self.session.flush()
        return attempt

    async def mark_succeeded(
        self, action: OutboxAction, provider_ref: str, provider_state: str
    ) -> None:
        """Mark action as successfully delivered with provider confirmation."""
        action.status = "SUCCEEDED"
        action.provider_ref = provider_ref
        action.provider_state = provider_state
        action.confirmed_at = datetime.now(UTC)
        action.readback_at = datetime.now(UTC)
        action.updated_at = datetime.now(UTC)
        action.lease_token = None
        action.lease_until = None
        await self.session.flush()

    async def get_attempts(
        self, tenant_id: str, client_id: UUID, action_id: UUID
    ) -> list[OutboxAttempt]:
        """Get all attempts for an action, ordered by attempt number."""
        stmt = (
            select(OutboxAttempt)
            .where(
                OutboxAttempt.tenant_id == tenant_id,
                OutboxAttempt.client_id == client_id,
                OutboxAttempt.action_id == action_id,
            )
            .order_by(OutboxAttempt.attempt_no)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
