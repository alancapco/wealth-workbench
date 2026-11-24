"""Action approval workflow endpoints."""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import AuthorizationError, check_permission
from app.core.database import get_db
from app.core.identity import get_fixture_identity, get_fixture_principal
from app.models.action import ActionAuthorization, ActionPreview, OutboxAction
from app.models.artifact import ArtifactRevision
from app.models.platform import ClientScope
from app.schemas.action import (
    CreateActionPreviewRequest,
    ActionPreviewResponse,
    AuthorizePreviewRequest,
    ActionAuthorizationResponse,
    ExecuteActionRequest,
    ActionResponse,
    AttemptSummary,
)
from app.schemas.common import Envelope, Environment, ResponseMeta
from app.services.actions.action_service import ActionService


router = APIRouter(prefix="/actions", tags=["actions"])


async def get_current_tenant_id() -> str:
    """Fixture tenant shared with the seeded clients/workflows."""
    return get_fixture_identity()[0]


async def get_current_user() -> str:
    """Fixture actor shared with the rest of the fixture data."""
    return get_fixture_identity()[1]


def _meta() -> ResponseMeta:
    return ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))


async def _check_access(
    db: AsyncSession,
    tenant_id: str,
    client_id: UUID,
    permission: str,
) -> None:
    """Fail closed on a missing grant or a client outside the caller's tenant scope."""
    principal = get_fixture_principal()
    if principal.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
    try:
        check_permission(principal, permission)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    in_scope = (await db.execute(
        select(ClientScope.client_id).where(
            ClientScope.tenant_id == tenant_id,
            ClientScope.client_id == client_id,
        )
    )).scalar_one_or_none()
    if in_scope is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client is outside the caller's scope",
        )


@router.post("/preview", status_code=status.HTTP_201_CREATED)
async def create_action_preview(
    request: CreateActionPreviewRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    actor: str = Depends(get_current_user),
) -> Envelope[ActionPreviewResponse]:
    """
    API-048: Create immutable action preview.
    
    Preview stores exact server-side payload and destination.
    No caller payload substitution at execution time.
    """
    service = ActionService(db)

    # The client is owned by the revision, never by a placeholder entity ID.
    ref = request.artifact_ref
    revision = (await db.execute(
        select(ArtifactRevision).where(
            ArtifactRevision.tenant_id == tenant_id,
            ArtifactRevision.id == ref.revision_id,
            ArtifactRevision.artifact_id == ref.artifact_id,
            ArtifactRevision.version == ref.version,
            ArtifactRevision.content_hash == ref.hash,
        )
    )).scalar_one_or_none()
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact revision not found",
        )
    await _check_access(db, tenant_id, revision.client_id, "action:preview")
    client_id = revision.client_id
    revision_id = revision.id

    approved_request = {
        "artifact_ref": {
            "artifact_id": str(ref.artifact_id),
            "revision_id": str(ref.revision_id),
            "version": ref.version,
            "hash": ref.hash,
        },
        "action_class": request.action_class,
    }

    # Mock provider/destination based on action class
    provider_key = f"mock-{request.action_class.lower()}-provider"
    destination_ref = "mock-destination"

    try:
        preview = await service.create_preview(
            tenant_id=tenant_id,
            client_id=client_id,
            revision_id=revision_id,
            action_class=request.action_class,
            approved_request=approved_request,
            provider_key=provider_key,
            destination_ref=destination_ref,
            environment_kind="FIXTURE",
            environment_id="test",
            context_revision=1,
            dependency_manifest={},
            created_by=actor,
        )

        response = ActionPreviewResponse(
            id=preview.id,
            artifact_ref=ref,
            action_class=preview.action_class,
            preview_hash=preview.preview_hash,
            environment=Environment(kind=preview.environment_kind, id=preview.environment_id),
            provider_key=preview.provider_key,
            destination_ref=preview.destination_ref,
            context_revision=preview.context_revision,
            created_at=preview.created_at,
            blockers=[],
        )

        return Envelope(data=response, meta=_meta())

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{preview_id}/authorize", status_code=status.HTTP_201_CREATED)
async def authorize_preview(
    preview_id: UUID,
    request: AuthorizePreviewRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    actor: str = Depends(get_current_user),
) -> Envelope[ActionAuthorizationResponse]:
    """
    API-049: Authorize preview by ID + hash.
    
    Authorization binds actor to exact preview content.
    Cannot edit payload - approves what was previewed.
    """
    service = ActionService(db)

    if not request.confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required"
        )

    preview = (await db.execute(
        select(ActionPreview).where(
            ActionPreview.tenant_id == tenant_id,
            ActionPreview.id == preview_id,
        )
    )).scalar_one_or_none()
    if preview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview not found")
    await _check_access(db, tenant_id, preview.client_id, "action:approve")

    try:
        authorization = await service.authorize_preview(
            tenant_id=tenant_id,
            client_id=preview.client_id,
            preview_id=preview_id,
            actor=actor,
        )

        response = ActionAuthorizationResponse(
            id=authorization.id,
            preview_id=authorization.preview_id,
            preview_hash=authorization.preview_hash,
            action_class=authorization.action_class,
            actor=authorization.actor,
            authorized_at=authorization.authorized_at,
            state=authorization.status,
        )

        return Envelope(data=response, meta=_meta())

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_action(
    request: ExecuteActionRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> Envelope[ActionResponse]:
    """
    API-011: Execute action by authorization_id only.
    
    No caller payload substitution - uses exact preview content.
    Returns 202 with action in PENDING status.
    """
    service = ActionService(db)

    authorization = (await db.execute(
        select(ActionAuthorization).where(
            ActionAuthorization.tenant_id == tenant_id,
            ActionAuthorization.id == request.authorization_id,
        )
    )).scalar_one_or_none()
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authorization not found",
        )
    await _check_access(db, tenant_id, authorization.client_id, "action:execute")

    try:
        action = await service.execute_action(
            tenant_id=tenant_id,
            authorization_id=request.authorization_id,
        )

        response = ActionResponse(
            id=action.id,
            authorization_id=action.authorization_id,
            action_class=authorization.action_class,
            status=action.status,
            provider_ref=action.provider_ref,
            provider_state=action.provider_state,
            created_at=action.created_at,
            submitted_at=action.submitted_at,
            confirmed_at=action.confirmed_at,
            readback_at=action.readback_at,
            error_code=action.last_error_code,
            can_reconcile=action.status in ["UNKNOWN", "RECONCILE_REQUIRED"],
            can_retry=action.status == "FAILED_SAFE",
            attempts=[],
        )

        return Envelope(data=response, meta=_meta())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/{action_id}")
async def get_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> Envelope[ActionResponse]:
    """
    API-012: Get action status.
    
    Read-only - no dispatch side effect.
    """
    service = ActionService(db)

    # Resolve the owner from the persisted action instead of a placeholder client.
    row = (await db.execute(
        select(OutboxAction.client_id, ActionAuthorization.action_class)
        .join(ActionAuthorization, and_(
            ActionAuthorization.tenant_id == OutboxAction.tenant_id,
            ActionAuthorization.client_id == OutboxAction.client_id,
            ActionAuthorization.id == OutboxAction.authorization_id,
        ))
        .where(
            OutboxAction.tenant_id == tenant_id,
            OutboxAction.id == action_id,
        )
    )).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
    client_id, action_class = row
    await _check_access(db, tenant_id, client_id, "action:execute")

    try:
        action, attempts = await service.get_action(tenant_id, client_id, action_id)

        attempt_summaries = [
            AttemptSummary(
                id=att.id,
                number=att.attempt_no,
                mode=att.mode,
                status=att.status,
                started_at=att.started_at,
                ended_at=att.ended_at,
                error_code=att.error_code,
                receipt_ref=att.receipt_ref,
            )
            for att in attempts
        ]

        response = ActionResponse(
            id=action.id,
            authorization_id=action.authorization_id,
            action_class=action_class,
            status=action.status,
            provider_ref=action.provider_ref,
            provider_state=action.provider_state,
            created_at=action.created_at,
            submitted_at=action.submitted_at,
            confirmed_at=action.confirmed_at,
            readback_at=action.readback_at,
            error_code=action.last_error_code,
            can_reconcile=action.status in ["UNKNOWN", "RECONCILE_REQUIRED"],
            can_retry=action.status == "FAILED_SAFE",
            attempts=attempt_summaries,
        )

        return Envelope(data=response, meta=_meta())

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
