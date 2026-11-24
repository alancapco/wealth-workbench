"""Message endpoints - generation and integration with action approval.

The read endpoint used to be a stub that always returned an empty list (and a
zero-UUID request_id). It now reads the current revision of every MESSAGE
artifact persisted for the workflow, so the messages panels show real drafts.
"""
from datetime import datetime, UTC
import json
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.artifact import ArtifactLineage, ArtifactRevision
from app.models.workflow import Workflow
from app.schemas.message import MessageGenerate, Message, MessageArtifactResponse, MessageEdit
from app.schemas.common import Envelope, ResponseMeta
from app.services.messaging.message_service import MessageService
from app.services.actions.action_service import ActionService


router = APIRouter(prefix="/workflows", tags=["messages"])

# Align with the tenant used by the seeded clients/workflows. The old
# "test-tenant" matched no row in workbench_tenants or client_scope.
FIXTURE_TENANT = "FIXTURE_TENANT_001"
FIXTURE_ACTOR = "fixture:rm001@example.test"


async def get_current_tenant_id() -> str:
    """Fixture tenant resolution (production would read the session principal)."""
    return FIXTURE_TENANT


async def get_current_user() -> str:
    """Fixture actor resolution."""
    return FIXTURE_ACTOR


def _meta() -> ResponseMeta:
    return ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))


def _not_found(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": code, "message": message, "retryable": False}},
    )


@router.get("/{workflow_id}/messages")
async def list_workflow_messages(
    workflow_id: UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List the current revision of each MESSAGE artifact for this workflow.

    Only the lineage's ``current_revision_id`` is returned: superseded drafts
    are immutable history, not the message the RM would send.
    """
    stmt = (
        select(ArtifactLineage, ArtifactRevision)
        .join(
            ArtifactRevision,
            and_(
                ArtifactRevision.tenant_id == ArtifactLineage.tenant_id,
                ArtifactRevision.client_id == ArtifactLineage.client_id,
                ArtifactRevision.artifact_id == ArtifactLineage.id,
                ArtifactRevision.id == ArtifactLineage.current_revision_id,
            ),
        )
        .where(
            ArtifactLineage.tenant_id == tenant_id,
            ArtifactLineage.workflow_id == workflow_id,
            ArtifactLineage.kind == "MESSAGE",
        )
        .order_by(ArtifactRevision.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()

    messages = []
    for lineage, revision in rows:
        try:
            payload = json.loads(revision.payload)
        except (TypeError, ValueError):
            payload = {}
        messages.append(
            {
                "artifact_id": str(lineage.id),
                "revision_id": str(revision.id),
                "version": revision.version,
                "kind": lineage.kind,
                "mode": payload.get("mode"),
                "channel": payload.get("channel"),
                "subject": payload.get("subject"),
                "body": payload.get("body"),
                "recipients": payload.get("recipients", []),
                "environment_kind": revision.environment_kind,
                "created_by": revision.created_by,
                "created_at": revision.created_at.isoformat() if revision.created_at else None,
            }
        )

    return {
        "data": {"messages": messages, "total": len(messages)},
        "meta": {"request_id": str(uuid4()), "served_at": datetime.now(UTC).isoformat()},
    }


@router.post("/{workflow_id}/messages", status_code=status.HTTP_201_CREATED)
async def generate_message(
    workflow_id: UUID,
    request: MessageGenerate,
    db: AsyncSession = Depends(get_db),
    actor: str = Depends(get_current_user),
) -> Envelope[MessageArtifactResponse]:
    """
    API-052: Generate message artifact from accepted items or priority reason.

    Creates immutable Message artifact stored in artifact_lineages/revisions.
    Message can then be previewed/authorized/executed via U-009 action framework.
    """
    # Resolve tenant/client from the real workflow instead of a mock zero UUID;
    # artifact_lineages has a composite FK to workflows(tenant_id, client_id, id).
    stmt = select(Workflow.tenant_id, Workflow.client_id).where(Workflow.id == workflow_id)
    row = (await db.execute(stmt)).first()
    if row is None:
        raise _not_found("WORKFLOW_NOT_FOUND", f"Workflow {workflow_id} was not found.")
    tenant_id, client_id = row

    service = MessageService(db)
    try:
        lineage, revision = await service.generate_message(
            tenant_id=tenant_id,
            client_id=client_id,
            workflow_id=workflow_id,
            request=request,
            actor=actor,
        )
        message = Message.model_validate(json.loads(revision.payload))
        response_data = MessageArtifactResponse(
            artifact_id=lineage.id,
            revision_id=revision.id,
            version=revision.version,
            message=message,
            created_at=revision.created_at,
            created_by=revision.created_by,
        )
        return Envelope(data=response_data, meta=_meta())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/messages/{artifact_id}", status_code=status.HTTP_201_CREATED)
async def edit_message(
    artifact_id: UUID,
    request: MessageEdit,
    db: AsyncSession = Depends(get_db),
    actor: str = Depends(get_current_user),
) -> Envelope[MessageArtifactResponse]:
    """
    Edit message artifact - creates new revision.

    Only recipients, subject, and body are editable.
    Editing invalidates any existing action previews (handled by action service).
    """
    stmt = (
        select(ArtifactLineage.tenant_id, ArtifactLineage.client_id)
        .where(ArtifactLineage.id == artifact_id, ArtifactLineage.kind == "MESSAGE")
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        raise _not_found("ARTIFACT_NOT_FOUND", f"Message artifact {artifact_id} was not found.")
    tenant_id, client_id = row

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
        message = Message.model_validate(json.loads(revision.payload))
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
        return Envelope(data=response_data, meta=_meta())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Note: Message send uses existing U-009 action framework:
# 1. POST /action-previews with artifact_ref + action_class=CLIENT_SEND
# 2. POST /action-previews/{id}/authorizations with preview_hash + confirmation
# 3. POST /actions with authorization_id only
# 4. GET /actions/{id} to check delivery status
#
# These endpoints are already implemented in backend/app/api/v1/endpoints/actions.py
