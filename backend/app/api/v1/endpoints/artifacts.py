"""Generic artifacts endpoints (API-045, API-046).

The router path is mounted with the /artifacts prefix, so the live route is
/api/v1/artifacts/artifacts/{id}. frontend/lib/endpoints.ts matches that
double-prefix convention - do not normalise one side alone.
"""
import hashlib
import json
from datetime import datetime, UTC
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentPrincipal, VerifiedCSRF
from app.core.database import get_db
from app.models.artifact import ArtifactDependency, ArtifactLineage, ArtifactRevision
from app.repositories.artifacts import RevisionRepository
from app.schemas.common import Envelope, ResponseMeta

router = APIRouter(tags=["artifacts"])


def _artifact_data(lineage: ArtifactLineage, revision: ArtifactRevision | None) -> dict:
    revision_data = None
    if revision:
        payload = revision.payload
        revision_data = {
            "id": str(revision.id),
            "version": revision.version,
            "content_hash": revision.content_hash,
            "payload": json.loads(payload) if isinstance(payload, str) else payload,
            "created_by": revision.created_by,
            "created_at": revision.created_at.isoformat(),
        }

    return {
        "id": str(lineage.id),
        "client_id": str(lineage.client_id),
        "workflow_id": str(lineage.workflow_id),
        "meeting_id": str(lineage.meeting_id) if lineage.meeting_id else None,
        "kind": lineage.kind,
        "current_revision": revision_data,
        "created_by": lineage.created_by,
        "created_at": lineage.created_at.isoformat(),
    }


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

    revision = None
    if lineage.current_revision_id:
        revision = (await db.execute(
            select(ArtifactRevision).where(
                ArtifactRevision.id == lineage.current_revision_id,
                ArtifactRevision.tenant_id == principal.tenant_id,
            )
        )).scalar_one_or_none()

    return Envelope(
        data=_artifact_data(lineage, revision),
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=principal.session_expires_at,
        ),
    )


@router.patch("/artifacts/{artifact_id}")
async def edit_artifact(
    artifact_id: UUID,
    principal: CurrentPrincipal,
    csrf: VerifiedCSRF,
    edit: dict | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Edit artifact by creating a new immutable revision (API-046).

    Edited fields are merged over the current payload; dependencies approved
    against prior revisions are invalidated.
    """
    lineage = (await db.execute(
        select(ArtifactLineage).where(
            ArtifactLineage.id == artifact_id,
            ArtifactLineage.tenant_id == principal.tenant_id,
        )
    )).scalar_one_or_none()

    if not lineage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Artifact not found"},
        )

    current = await RevisionRepository(db).get_current_revision(
        principal.tenant_id, lineage.client_id, lineage.id
    )

    edit = edit or {}
    new_payload = edit.get("payload", {k: v for k, v in edit.items() if k != "reason"})
    if not isinstance(new_payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_PAYLOAD", "message": "Payload must be an object"},
        )

    if current:
        current_payload = current.payload
        base = json.loads(current_payload) if isinstance(current_payload, str) else current_payload
        if isinstance(base, dict):
            new_payload = {**base, **new_payload}

    # Canonical JSON matches MessageService/ActionService hashing so If-Match
    # and revision hashes agree across the artifact chain.
    canonical = json.dumps(new_payload, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    revision = ArtifactRevision(
        id=uuid4(),
        tenant_id=lineage.tenant_id,
        client_id=lineage.client_id,
        artifact_id=lineage.id,
        version=current.version + 1 if current else 1,
        content_hash=content_hash,
        payload=canonical,
        environment_kind=principal.environment.kind.value,
        environment_id=principal.environment.id,
        created_by=principal.subject,
        created_at=datetime.now(UTC),
    )

    # A dependent revision approved against an old basis must not remain valid
    # after this artifact changes; the schema has no invalidation flag, so drop
    # the stale dependency links.
    await db.execute(
        delete(ArtifactDependency).where(
            ArtifactDependency.tenant_id == lineage.tenant_id,
            ArtifactDependency.client_id == lineage.client_id,
            ArtifactDependency.basis_revision_id.in_(
                select(ArtifactRevision.id).where(
                    ArtifactRevision.tenant_id == lineage.tenant_id,
                    ArtifactRevision.client_id == lineage.client_id,
                    ArtifactRevision.artifact_id == lineage.id,
                )
            ),
        )
    )

    db.add(revision)
    lineage.current_revision_id = revision.id
    data = _artifact_data(lineage, revision)
    await db.commit()

    return Envelope(
        data=data,
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=principal.session_expires_at,
        ),
    )
