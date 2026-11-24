"""Meetings endpoint (API-024).

The router path is mounted with the /meetings prefix, so the live route is
/api/v1/meetings/meetings/{id}. frontend/lib/endpoints.ts matches that
double-prefix convention - do not normalise one side alone.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4

from app.api.dependencies import CurrentPrincipal
from app.core.database import get_db
from app.models.artifact import ArtifactLineage, ArtifactRevision, RevisionSource, SourceEvidence
from app.models.workflow import Meeting as MeetingModel, Workflow
from app.schemas.calendar import Meeting
from app.schemas.common import Envelope, EvidenceRef, ResponseMeta

router = APIRouter(tags=["meetings"])


async def load_meeting_refs(
    db: AsyncSession, tenant_id: str, meeting_id: UUID
) -> tuple[list[UUID], list[EvidenceRef]]:
    """Load workflows and source evidence attached to a meeting.

    Evidence is linked through revision_sources of the meeting's artifacts,
    including artifacts produced by any workflow resumed from that meeting.
    """
    workflow_ids = list((await db.scalars(
        select(Workflow.id).where(
            Workflow.tenant_id == tenant_id,
            Workflow.meeting_id == meeting_id,
        )
    )).all())

    rows = (await db.execute(
        select(RevisionSource.source_id, SourceEvidence.record_version)
        .join(
            ArtifactRevision,
            and_(
                ArtifactRevision.id == RevisionSource.revision_id,
                ArtifactRevision.tenant_id == RevisionSource.tenant_id,
                ArtifactRevision.client_id == RevisionSource.client_id,
            ),
        )
        .join(
            ArtifactLineage,
            and_(
                ArtifactLineage.id == ArtifactRevision.artifact_id,
                ArtifactLineage.tenant_id == ArtifactRevision.tenant_id,
                ArtifactLineage.client_id == ArtifactRevision.client_id,
            ),
        )
        .join(
            SourceEvidence,
            and_(
                SourceEvidence.id == RevisionSource.source_id,
                SourceEvidence.tenant_id == RevisionSource.tenant_id,
                SourceEvidence.client_id == RevisionSource.client_id,
            ),
        )
        .where(
            ArtifactLineage.tenant_id == tenant_id,
            or_(
                ArtifactLineage.meeting_id == meeting_id,
                ArtifactLineage.workflow_id.in_(workflow_ids),
            ),
        )
        .distinct()
    )).all()

    source_refs = [EvidenceRef(source_id=r[0], source_version=r[1]) for r in rows]
    return workflow_ids, source_refs


@router.get("/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: UUID,
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[Meeting]:
    """Get meeting detail (API-024).

    Returns meeting with resolution, calendar event linkage, and workflow IDs.
    """
    stmt = select(MeetingModel).where(
        MeetingModel.id == meeting_id,
        MeetingModel.tenant_id == principal.tenant_id,
    )
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Meeting not found"},
        )

    workflow_ids, source_refs = await load_meeting_refs(db, principal.tenant_id, meeting.id)

    meeting_data = Meeting(
        id=meeting.id,
        client_id=meeting.client_id,
        calendar_event_id=meeting.calendar_event_id,
        event_version=meeting.event_version,
        resolution=meeting.resolution,
        title=meeting.title,
        start=meeting.starts_at,
        end=meeting.ends_at,
        workflow_ids=workflow_ids,
        row_version=meeting.row_version,
        source_refs=source_refs,
    )

    return Envelope(
        data=meeting_data,
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=principal.session_expires_at,
        ),
    )
