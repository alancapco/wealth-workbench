"""Message endpoints - generation and integration with action approval."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.message import MessageGenerate, Message, MessageArtifactResponse, MessageEdit
from app.schemas.common import Envelope, ResponseMeta, ArtifactRef
from app.schemas.action import CreateActionPreviewRequest, ActionPreviewResponse
from app.services.messaging.message_service import MessageService
from app.services.actions.action_service import ActionService


router = APIRouter(prefix="/workflows", tags=["messages"])


# Mock dependencies - real implementation would use auth
async def get_current_tenant_id() -> str:
    """Mock tenant resolution."""
    return "test-tenant"


async def get_current_client_id() -> UUID:
    """Mock client resolution."""
    return UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user() -> str:
    """Mock user resolution."""
    return "test-user"


@router.post("/{workflow_id}/messages", status_code=status.HTTP_201_CREATED)
async def generate_message(
    workflow_id: UUID,
    request: MessageGenerate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    client_id: UUID = Depends(get_current_client_id),
    actor: str = Depends(get_current_user),
) -> Envelope[MessageArtifactResponse]:
    """
    API-052: Generate message artifact from accepted items or priority reason.
    
    Creates immutable Message artifact stored in artifact_lineages/revisions.
    Message can then be previewed/authorized/executed via U-009 action framework.
    """
    service = MessageService(db)
    
    try:
        lineage, revision = await service.generate_message(
            tenant_id=tenant_id,
            client_id=client_id,
            workflow_id=workflow_id,
            request=request,
            actor=actor,
        )
        
        # Parse message from revision payload
        import json
        message = Message.model_validate(json.loads(revision.payload))
        
        response_data = MessageArtifactResponse(
            artifact_id=lineage.id,
            revision_id=revision.id,
            version=revision.version,
            message=message,
            created_at=revision.created_at,
            created_by=revision.created_by,
        )
        
        return Envelope(
            data=response_data,
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000000"),  # Mock
                served_at=revision.created_at,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/messages/{artifact_id}", status_code=status.HTTP_201_CREATED)
async def edit_message(
    artifact_id: UUID,
    request: MessageEdit,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    client_id: UUID = Depends(get_current_client_id),
    actor: str = Depends(get_current_user),
) -> Envelope[MessageArtifactResponse]:
    """
    Edit message artifact - creates new revision.
    
    Only recipients, subject, and body are editable.
    Editing invalidates any existing action previews (handled by action service).
    """
    service = MessageService(db)
    
    try:
        revision = await service.edit_message(
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=artifact_id,
            recipients=request.recipients,
            subject=request.subject,
            body=request.body,
            actor=actor,
        )
        
        # Parse message from revision payload
        import json
        message = Message.model_validate(json.loads(revision.payload))
        
        # Invalidate previews for this revision
        action_service = ActionService(db)
        await action_service.invalidate_previews_by_revision(
            tenant_id, client_id, revision.id
        )
        
        response_data = MessageArtifactResponse(
            artifact_id=artifact_id,
            revision_id=revision.id,
            version=revision.version,
            message=message,
            created_at=revision.created_at,
            created_by=revision.created_by,
        )
        
        return Envelope(
            data=response_data,
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000000"),  # Mock
                served_at=revision.created_at,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Note: Message send uses existing U-009 action framework:
# 1. POST /action-previews with artifact_ref + action_class=CLIENT_SEND
# 2. POST /action-previews/{id}/authorizations with preview_hash + confirmation
# 3. POST /actions with authorization_id only
# 4. GET /actions/{id} to check delivery status
#
# These endpoints are already implemented in backend/app/api/v1/endpoints/actions.py
