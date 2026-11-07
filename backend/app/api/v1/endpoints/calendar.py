"""Calendar events endpoints (API-022, API-023)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.dependencies import CurrentPrincipal, VerifiedCSRF
from app.core.database import get_db
from app.models.workflow import CalendarEvent as CalendarEventModel
from app.schemas.calendar import CalendarEventListData, EventResolutionRequest
from app.schemas.common import CapabilityState, Envelope, ResponseMeta

router = APIRouter(tags=["calendar"])


@router.get("/calendar/events")
async def list_calendar_events(
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[CalendarEventListData]:
    """List calendar events (API-022).
    
    Returns calendar events with match state and resolved meetings.
    Capability state indicates if calendar integration is configured.
    """
    # Check if calendar is configured - placeholder for now
    capability_state = CapabilityState.UNCONFIGURED
    
    # TODO: Query calendar_events table filtered by tenant and actor
    # For now return empty list with UNCONFIGURED state
    
    data = CalendarEventListData(
        items=[],
        next_cursor=None,
        capability_state=capability_state,
    )
    
    return Envelope(
        data=data,
        meta=ResponseMeta(
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=principal.session_expires_at,
        ),
    )


@router.post("/calendar/events/{event_id}/resolutions")
async def resolve_calendar_event(
    event_id: UUID,
    resolution: EventResolutionRequest,
    principal: CurrentPrincipal,
    csrf: VerifiedCSRF,
    db: AsyncSession = Depends(get_db),
):
    """Resolve calendar event to client and create meeting (API-023).
    
    Requires:
    - event_version: provider version for optimistic locking
    - client_id: resolved client UUID
    - confirmation: true to confirm match
    
    Creates Meeting record and links to workflow.
    """
    # TODO: Implement calendar event resolution
    # 1. Verify event_id exists and version matches
    # 2. Create Meeting record with resolution=VERIFIED or RM_CONFIRMED
    # 3. Update calendar event match_state
    # 4. Return created meeting
    
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "UNCONFIGURED", "message": "Calendar integration not configured"},
    )
