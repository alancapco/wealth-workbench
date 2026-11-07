"""Action approval workflow endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.action import (
    CreateActionPreviewRequest,
    ActionPreviewResponse,
    AuthorizePreviewRequest,
    ActionAuthorizationResponse,
    ExecuteActionRequest,
    ActionResponse,
    ReconcileActionRequest,
    RetryActionRequest,
    AttemptSummary,
)
from app.schemas.common import Envelope, Environment, Blocker
from app.services.actions.action_service import ActionService


router = APIRouter(prefix="/actions", tags=["actions"])


# Mock dependencies - real implementation would use auth
async def get_current_tenant_id() -> str:
    """Mock tenant resolution."""
    return "test-tenant"


async def get_current_user() -> str:
    """Mock user resolution."""
    return "test-user"


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
    
    # Mock: extract client_id from artifact_ref
    # Real implementation would resolve artifact and validate permissions
    client_id = UUID("00000000-0000-0000-0000-000000000001")
    revision_id = request.artifact_ref.revision_id
    
    # Mock approved request - real implementation would build from artifact
    approved_request = {
        "artifact_ref": {
            "artifact_id": str(request.artifact_ref.artifact_id),
            "revision_id": str(request.artifact_ref.revision_id),
            "version": request.artifact_ref.version,
            "hash": request.artifact_ref.hash,
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
            artifact_ref=request.artifact_ref,
            action_class=preview.action_class,
            preview_hash=preview.preview_hash,
            environment=Environment(kind=preview.environment_kind, id=preview.environment_id),
            provider_key=preview.provider_key,
            destination_ref=preview.destination_ref,
            context_revision=preview.context_revision,
            created_at=preview.created_at,
            blockers=[],
        )
        
        return Envelope(data=response)
        
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
    
    # Mock client_id resolution
    client_id = UUID("00000000-0000-0000-0000-000000000001")
    
    try:
        authorization = await service.authorize_preview(
            tenant_id=tenant_id,
            client_id=client_id,
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
        
        return Envelope(data=response)
        
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
    
    try:
        action = await service.execute_action(
            tenant_id=tenant_id,
            authorization_id=request.authorization_id,
        )
        
        response = ActionResponse(
            id=action.id,
            authorization_id=action.authorization_id,
            action_class="CRM_WRITE",  # Would come from authorization
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
        
        return Envelope(data=response)
        
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
    
    # Mock client_id
    client_id = UUID("00000000-0000-0000-0000-000000000001")
    
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
            action_class="CRM_WRITE",  # Would come from authorization
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
        
        return Envelope(data=response)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
