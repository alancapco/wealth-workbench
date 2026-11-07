"""Action service for preview creation, authorization validation, and execution."""
import hashlib
import json
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ActionPreview, ActionAuthorization, OutboxAction
from app.repositories.outbox import (
    ActionPreviewRepository,
    ActionAuthorizationRepository,
    OutboxRepository,
)


class ActionService:
    """
    Core action approval workflow:
    1. Create immutable server-side preview with exact payload/destination
    2. Authorization references preview by ID + hash
    3. Execute accepts only authorization_id (no caller payload substitution)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.preview_repo = ActionPreviewRepository(session)
        self.auth_repo = ActionAuthorizationRepository(session)
        self.outbox_repo = OutboxRepository(session)

    def _compute_hash(self, data: dict) -> str:
        """Compute SHA-256 hash of canonical JSON."""
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    async def create_preview(
        self,
        tenant_id: str,
        client_id: UUID,
        revision_id: UUID,
        action_class: str,
        approved_request: dict,
        provider_key: str,
        destination_ref: str,
        environment_kind: str,
        environment_id: str,
        context_revision: int,
        dependency_manifest: dict,
        created_by: str,
    ) -> ActionPreview:
        """
        Create immutable action preview.
        Preview stores exact server-side payload and destination.
        """
        # Compute hashes
        request_hash = self._compute_hash(approved_request)
        preview_content = {
            "revision_id": str(revision_id),
            "action_class": action_class,
            "request": approved_request,
            "provider_key": provider_key,
            "destination_ref": destination_ref,
            "environment": {"kind": environment_kind, "id": environment_id},
            "context_revision": context_revision,
            "dependencies": dependency_manifest,
        }
        preview_hash = self._compute_hash(preview_content)

        # Store preview
        preview = await self.preview_repo.create_preview(
            tenant_id=tenant_id,
            client_id=client_id,
            revision_id=revision_id,
            action_class=action_class,
            preview_hash=preview_hash,
            request_hash=request_hash,
            approved_request=json.dumps(approved_request),
            provider_key=provider_key,
            destination_ref=destination_ref,
            environment_kind=environment_kind,
            environment_id=environment_id,
            context_revision=context_revision,
            dependency_manifest=json.dumps(dependency_manifest),
            created_by=created_by,
        )
        await self.session.commit()
        return preview

    async def authorize_preview(
        self,
        tenant_id: str,
        client_id: UUID,
        preview_id: UUID,
        actor: str,
    ) -> ActionAuthorization:
        """
        Create authorization binding actor to exact preview hash.
        Authorization cannot edit content - it approves the exact preview.
        """
        # Get preview and validate it's still valid
        preview = await self.preview_repo.get_by_id(tenant_id, client_id, preview_id)
        if not preview:
            raise ValueError("Preview not found")
        if preview.status != "VALID":
            raise ValueError(f"Preview is {preview.status}, cannot authorize")

        # Create authorization
        authorization = await self.auth_repo.authorize_preview(
            tenant_id=tenant_id,
            client_id=client_id,
            preview_id=preview_id,
            preview_hash=preview.preview_hash,
            action_class=preview.action_class,
            actor=actor,
        )
        await self.session.commit()
        return authorization

    async def execute_action(
        self,
        tenant_id: str,
        authorization_id: UUID,
    ) -> OutboxAction:
        """
        Execute action by authorization_id only.
        No caller payload substitution - uses exact preview content.
        Creates outbox action transactionally.
        """
        # Find authorization
        stmt_auth = await self.session.execute(
            f"SELECT * FROM action_authorizations WHERE tenant_id = :tenant_id AND id = :auth_id",
            {"tenant_id": tenant_id, "auth_id": authorization_id}
        )
        # Proper query using repository
        authorization = await self.auth_repo.get_by_id(tenant_id, None, authorization_id)
        if not authorization:
            raise ValueError("Authorization not found")
        if authorization.status != "VALID":
            raise ValueError(f"Authorization is {authorization.status}, cannot execute")

        # Get preview
        preview = await self.preview_repo.get_by_id(
            tenant_id, authorization.client_id, authorization.preview_id
        )
        if not preview:
            raise ValueError("Preview not found")
        if preview.status != "VALID":
            raise ValueError(f"Preview is {preview.status}, cannot execute")

        # Verify hash match
        if preview.preview_hash != authorization.preview_hash:
            raise ValueError("Preview hash mismatch - content changed")

        # Create provider operation key (stable, reused for idempotency)
        provider_operation_key = f"{preview.provider_key}:{authorization.id}"

        # Enqueue action
        action = await self.outbox_repo.enqueue_action(
            tenant_id=tenant_id,
            client_id=authorization.client_id,
            authorization_id=authorization_id,
            provider_operation_key=provider_operation_key,
        )
        await self.session.commit()
        return action

    async def get_action(
        self, tenant_id: str, client_id: UUID, action_id: UUID
    ) -> tuple[OutboxAction, list]:
        """Get action with attempts. Read-only - no dispatch side effect."""
        action = await self.outbox_repo.get_by_id(tenant_id, client_id, action_id)
        if not action:
            raise ValueError("Action not found")
        
        attempts = await self.outbox_repo.get_attempts(tenant_id, client_id, action_id)
        return action, attempts

    async def invalidate_previews_by_revision(
        self, tenant_id: str, client_id: UUID, revision_id: UUID
    ) -> int:
        """Invalidate all previews when artifact revision changes."""
        count = await self.preview_repo.invalidate_by_revision(
            tenant_id, client_id, revision_id
        )
        await self.session.commit()
        return count
