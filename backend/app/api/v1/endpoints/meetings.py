"""Meetings endpoint (API-024)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.dependencies import CurrentPrincipal
from app.core.database import get_db
from app.models.workflow import Meeting as MeetingModel
from app.schemas.calendar import Meeting
from app.schemas.common import Envelope, ResponseMeta

router = APIRouter(tags=["meetings"])


@router.get("/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: UUID,
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[Meeting]:
    """Get meeting detail (API-024).
    
    Returns meeting with resolution, calendar event linkage, and workflow IDs.
    """
    # Query meeting by ID and tenant
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
    
    # TODO: Query associated workflows
    workflow_ids = []
    
    # TODO: Query source evidence for source_refs
    source_refs = []
    
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
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=principal.session_expires_at,
        ),
    )
