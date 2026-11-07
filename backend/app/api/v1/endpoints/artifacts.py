"""Generic artifacts endpoints (API-045, API-046)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.dependencies import CurrentPrincipal, VerifiedCSRF
from app.core.database import get_db
from app.models.artifact import ArtifactLineage, ArtifactRevision
from app.schemas.common import Envelope, ResponseMeta

router = APIRouter(tags=["artifacts"])


@router.get("/artifacts/{artifact_id}")
async def get_artifact(
    artifact_id: UUID,
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Get artifact with current revision (API-045).
    
    Returns artifact lineage with current revision payload.
    Used for briefs, transcripts, extractions, and other workflow artifacts.
    """
    # Query artifact lineage
    stmt = select(ArtifactLineage).where(
        ArtifactLineage.id == artifact_id,
        ArtifactLineage.tenant_id == principal.tenant_id,
    )
    result = await db.execute(stmt)
    lineage = result.scalar_one_or_none()
    
    if not lineage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Artifact not found"},
        )
    
    # Query current revision if exists
    revision_data = None
    if lineage.current_revision_id:
        stmt = select(ArtifactRevision).where(
            ArtifactRevision.id == lineage.current_revision_id,
            ArtifactRevision.tenant_id == principal.tenant_id,
        )
        result = await db.execute(stmt)
        revision = result.scalar_one_or_none()
        
        if revision:
            import json
            revision_data = {
                "id": str(revision.id),
                "version": revision.version,
                "content_hash": revision.content_hash,
                "payload": json.loads(revision.payload),
                "created_by": revision.created_by,
                "created_at": revision.created_at.isoformat(),
            }
    
    artifact_data = {
        "id": str(lineage.id),
        "client_id": str(lineage.client_id),
        "workflow_id": str(lineage.workflow_id),
        "meeting_id": str(lineage.meeting_id) if lineage.meeting_id else None,
        "kind": lineage.kind,
        "current_revision": revision_data,
        "created_by": lineage.created_by,
        "created_at": lineage.created_at.isoformat(),
    }
    
    return Envelope(
        data=artifact_data,
        meta=ResponseMeta(
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=principal.session_expires_at,
        ),
    )


@router.patch("/artifacts/{artifact_id}")
async def edit_artifact(
    artifact_id: UUID,
    principal: CurrentPrincipal,
    csrf: VerifiedCSRF,
    db: AsyncSession = Depends(get_db),
):
    """Edit artifact by creating new revision (API-046).
    
    Creates new artifact revision with edited content.
    Requires review approval for regulated artifact types.
    """
    # TODO: Implement artifact editing
    # 1. Verify artifact_id exists and belongs to principal's tenant
    # 2. Create new ArtifactRevision with incremented version
    # 3. Update ArtifactLineage.current_revision_id
    # 4. Handle item-level reviews if needed
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"code": "NOT_IMPLEMENTED", "message": "Artifact editing not yet implemented"},
    )
