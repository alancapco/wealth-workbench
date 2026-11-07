"""Outbox worker for claiming pending actions and managing lease lifecycle."""
from datetime import datetime, UTC, timedelta
from uuid import UUID, uuid4
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import OutboxAction, ActionPreview, ActionAuthorization
from app.repositories.outbox import OutboxRepository


class OutboxWorker:
    """
    Background worker for action dispatch with lease management and crash recovery.
    
    Workflow:
    1. Claim pending actions with FOR UPDATE SKIP LOCKED
    2. Assign lease token and lease_until
    3. Record attempt (DISPATCH or READBACK mode)
    4. Execute with provider (not implemented in this unit - uses adapters)
    5. Update status based on result:
       - CONFIRMED receipt + readback → SUCCEEDED
       - NOT_ACCEPTED → FAILED_SAFE
       - Timeout/crash → UNKNOWN (never blind resend)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.outbox_repo = OutboxRepository(session)

    async def claim_actions(
        self, lease_duration_seconds: int = 300, limit: int = 10
    ) -> list[OutboxAction]:
        """
        Claim pending/expired actions with lease for processing.
        Returns actions needing dispatch or reconciliation.
        """
        actions = await self.outbox_repo.claim_next_pending(
            lease_duration_seconds=lease_duration_seconds, limit=limit
        )
        await self.session.commit()
        return actions

    async def record_dispatch_started(
        self, action: OutboxAction, lease_token: UUID, request_hash: str
    ) -> None:
        """Record dispatch attempt started."""
        attempt_no = action.attempt_count + 1
        await self.outbox_repo.record_attempt(
            action=action,
            attempt_no=attempt_no,
            mode="DISPATCH",
            lease_token=lease_token,
            status="STARTED",
            request_hash=request_hash,
        )
        action.status = "SENDING"
        await self.session.commit()

    async def record_dispatch_confirmed(
        self,
        action: OutboxAction,
        lease_token: UUID,
        request_hash: str,
        receipt_ref: str,
    ) -> None:
        """Record successful dispatch with provider receipt."""
        attempt_no = action.attempt_count
        await self.outbox_repo.record_attempt(
            action=action,
            attempt_no=attempt_no,
            mode="DISPATCH",
            lease_token=lease_token,
            status="CONFIRMED",
            request_hash=request_hash,
            receipt_ref=receipt_ref,
        )
        # Status stays SENDING until readback confirms
        await self.session.commit()

    async def record_dispatch_not_accepted(
        self,
        action: OutboxAction,
        lease_token: UUID,
        request_hash: str,
        error_code: str,
    ) -> None:
        """Record authoritative NOT_ACCEPTED from provider."""
        attempt_no = action.attempt_count
        await self.outbox_repo.record_attempt(
            action=action,
            attempt_no=attempt_no,
            mode="DISPATCH",
            lease_token=lease_token,
            status="NOT_ACCEPTED",
            request_hash=request_hash,
            error_code=error_code,
        )
        await self.session.commit()

    async def mark_unknown_on_timeout(
        self,
        action: OutboxAction,
        lease_token: UUID,
        request_hash: str,
        error_code: str,
    ) -> None:
        """
        Mark action as UNKNOWN on timeout/crash.
        Safety beats assumed retry - any uncertainty becomes UNKNOWN.
        Requires readback reconciliation.
        """
        attempt_no = action.attempt_count
        await self.outbox_repo.record_attempt(
            action=action,
            attempt_no=attempt_no,
            mode="DISPATCH",
            lease_token=lease_token,
            status="UNKNOWN",
            request_hash=request_hash,
            error_code=error_code,
        )
        await self.session.commit()

    async def mark_succeeded(
        self,
        action: OutboxAction,
        provider_ref: str,
        provider_state: str,
    ) -> None:
        """
        Mark action SUCCEEDED after confirmed receipt + required readback.
        Only call after authoritative provider confirmation.
        """
        await self.outbox_repo.mark_succeeded(
            action=action,
            provider_ref=provider_ref,
            provider_state=provider_state,
        )
        await self.session.commit()

    async def record_readback_attempt(
        self,
        action: OutboxAction,
        lease_token: UUID,
        request_hash: str,
        status: str,
        receipt_ref: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """Record readback reconciliation attempt."""
        attempt_no = action.attempt_count + 1
        await self.outbox_repo.record_attempt(
            action=action,
            attempt_no=attempt_no,
            mode="READBACK",
            lease_token=lease_token,
            status=status,
            request_hash=request_hash,
            receipt_ref=receipt_ref,
            error_code=error_code,
        )
        
        if status == "CONFIRMED" and receipt_ref:
            # Readback confirmed - can mark succeeded
            action.status = "SUCCEEDED"
            action.provider_ref = receipt_ref
            action.readback_at = datetime.now(UTC)
        elif status == "NOT_ACCEPTED":
            action.status = "FAILED_SAFE"
            action.last_error_code = error_code
        elif status == "UNKNOWN":
            # Still unknown after readback
            action.status = "RECONCILE_REQUIRED"
            action.last_error_code = error_code
        
        await self.session.commit()

    async def get_action_with_preview(
        self, tenant_id: str, client_id: UUID, action_id: UUID
    ) -> tuple[OutboxAction, ActionAuthorization, ActionPreview]:
        """Get action with authorization and preview for execution."""
        action = await self.outbox_repo.get_by_id(tenant_id, client_id, action_id)
        if not action:
            raise ValueError("Action not found")

        # Get authorization
        from sqlalchemy import select
        stmt = select(ActionAuthorization).where(
            ActionAuthorization.tenant_id == tenant_id,
            ActionAuthorization.id == action.authorization_id,
        )
        result = await self.session.execute(stmt)
        authorization = result.scalar_one_or_none()
        if not authorization:
            raise ValueError("Authorization not found")

        # Get preview
        stmt = select(ActionPreview).where(
            ActionPreview.tenant_id == tenant_id,
            ActionPreview.id == authorization.preview_id,
        )
        result = await self.session.execute(stmt)
        preview = result.scalar_one_or_none()
        if not preview:
            raise ValueError("Preview not found")

        return action, authorization, preview
