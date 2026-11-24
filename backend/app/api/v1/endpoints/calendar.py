"""Calendar events endpoints (API-022, API-023).

The router path is mounted with the /calendar prefix, so the live routes are
/api/v1/calendar/calendar/events and .../resolutions. frontend/lib/endpoints.ts
matches that double-prefix convention - do not normalise one side alone.
"""
import json
from datetime import datetime, UTC
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentPrincipal, VerifiedCSRF
from app.api.v1.endpoints.meetings import load_meeting_refs
from app.core.database import get_db
from app.models.platform import ClientScope
from app.models.workflow import CalendarEvent as CalendarEventModel, Meeting as MeetingModel
from app.schemas.calendar import (
    CalendarEvent as CalendarEventDTO,
    CalendarEventListData,
    CalendarEventStatus,
    EventResolutionRequest,
    MatchState,
    Meeting as MeetingDTO,
    MeetingResolution,
)
from app.schemas.client import ClientSummary
from app.schemas.common import (
    Availability,
    CapabilityState,
    Envelope,
    Origin,
    ResponseMeta,
    Scope,
    Source,
)
from app.services.config.config_service import ConfigService

router = APIRouter(tags=["calendar"])


def _payload(event: CalendarEventModel) -> dict:
    raw = event.payload
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return raw if isinstance(raw, dict) else {}


def _parse_time(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _calendar_event_dto(
    event: CalendarEventModel,
    principal: CurrentPrincipal,
    resolved_meeting_id: UUID | None,
) -> CalendarEventDTO:
    payload = _payload(event)
    start = _parse_time(payload.get("start") or payload.get("starts_at"))
    end = _parse_time(payload.get("end") or payload.get("ends_at"))
    limitations = []
    if start is None or end is None:
        # Provider payload without event times: API-022 requires timestamps, so
        # surface the retrieval time with an explicit limitation rather than
        # inventing a schedule.
        limitations.append("EVENT_TIMES_UNAVAILABLE")
        start = start or event.retrieved_at
        end = end or start

    hints = payload.get("attendee_hints")
    candidates = []
    for candidate in payload.get("candidates") or []:
        try:
            candidates.append(ClientSummary.model_validate(candidate))
        except ValidationError:
            # Provider hints without a full client summary are not candidates.
            continue

    source = Source(
        id=event.id,
        environment=principal.environment,
        availability=Availability.AVAILABLE if event.status == "ACTIVE" else Availability.UNAVAILABLE,
        origin=Origin.RECORDED,
        system_key=event.provider_key,
        record_id=event.provider_event_id,
        record_version=event.provider_version,
        as_of=event.retrieved_at,
        retrieved_at=event.retrieved_at,
        live_response=False,
        limitation_codes=limitations,
    )

    return CalendarEventDTO(
        id=event.id,
        provider_event_id=event.provider_event_id,
        provider_version=event.provider_version,
        title=payload.get("title") or event.provider_event_id,
        start=start,
        end=end,
        status=CalendarEventStatus(event.status),
        attendee_hints=[str(h) for h in hints] if isinstance(hints, list) else [],
        match_state=MatchState(event.match_state),
        candidates=candidates,
        resolved_meeting_id=resolved_meeting_id,
        source=source,
    )


@router.get("/calendar/events")
async def list_calendar_events(
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[CalendarEventListData]:
    """List calendar events (API-022).

    Returns calendar events with match state and resolved meetings.
    Capability state indicates if calendar integration is configured.
    """
    config = await ConfigService(db).get_provider_config(
        Scope(tenant_id=principal.tenant_id), "calendar"
    )
    if config is None:
        capability_state = CapabilityState.UNCONFIGURED
    elif config.get("enabled") is False or config.get("enabled") == "false":
        capability_state = CapabilityState.DISABLED
    elif config.get("state") == "UNAVAILABLE":
        capability_state = CapabilityState.UNAVAILABLE
    else:
        capability_state = CapabilityState.READY

    events = list((await db.scalars(
        select(CalendarEventModel)
        .where(
            CalendarEventModel.tenant_id == principal.tenant_id,
            CalendarEventModel.actor_subject == principal.subject,
        )
        .order_by(CalendarEventModel.retrieved_at.desc())
    )).all())

    event_ids = [event.id for event in events]
    resolved_map: dict[UUID, UUID] = {}
    if event_ids:
        rows = (await db.execute(
            select(MeetingModel.calendar_event_id, MeetingModel.id).where(
                MeetingModel.tenant_id == principal.tenant_id,
                MeetingModel.calendar_event_id.in_(event_ids),
            )
        )).all()
        resolved_map = {row[0]: row[1] for row in rows}

    data = CalendarEventListData(
        items=[_calendar_event_dto(event, principal, resolved_map.get(event.id)) for event in events],
        next_cursor=None,
        capability_state=capability_state,
    )

    return Envelope(
        data=data,
        meta=ResponseMeta(
            request_id=uuid4(),
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
) -> Envelope[dict]:
    """Resolve calendar event to client and create meeting (API-023).

    Requires:
    - event_version: provider version for optimistic locking
    - client_id: resolved client UUID
    - confirmation: true to confirm match

    Creates Meeting record and links to workflow.
    """
    event = (await db.execute(
        select(CalendarEventModel).where(
            CalendarEventModel.id == event_id,
            CalendarEventModel.tenant_id == principal.tenant_id,
        )
    )).scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Calendar event not found"},
        )

    # Optimistic lock: the provider version the RM saw must still be current.
    if event.provider_version != resolution.event_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "STALE_EVENT_VERSION", "message": "Calendar event version has changed"},
        )
    if event.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EVENT_NOT_ACTIVE", "message": "Only active events can be resolved"},
        )
    if not resolution.confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONFIRMATION_REQUIRED", "message": "Resolution must be confirmed"},
        )

    # A second resolution must not create a duplicate meeting for one event.
    existing_meeting_id = await db.scalar(
        select(MeetingModel.id).where(
            MeetingModel.tenant_id == principal.tenant_id,
            MeetingModel.calendar_event_id == event.id,
        )
    )
    if existing_meeting_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EVENT_ALREADY_RESOLVED", "message": "Calendar event already resolved"},
        )

    # meetings has a composite FK to client_scope; reject unknown clients up front.
    client_in_scope = await db.scalar(
        select(ClientScope.client_id).where(
            ClientScope.tenant_id == principal.tenant_id,
            ClientScope.client_id == resolution.client_id,
        )
    )
    if client_in_scope is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CLIENT_NOT_FOUND", "message": "Client not in tenant scope"},
        )

    payload = _payload(event)
    meeting = MeetingModel(
        id=uuid4(),
        tenant_id=principal.tenant_id,
        client_id=resolution.client_id,
        calendar_event_id=event.id,
        event_version=event.provider_version,
        resolution="VERIFIED" if event.match_state == "VERIFIED" else "RM_CONFIRMED",
        title=payload.get("title") or event.provider_event_id,
        starts_at=_parse_time(payload.get("start") or payload.get("starts_at")),
        ends_at=_parse_time(payload.get("end") or payload.get("ends_at")),
        row_version=1,
        resolved_by=principal.subject,
        resolved_at=datetime.now(UTC),
    )
    db.add(meeting)
    event.match_state = "VERIFIED"
    await db.flush()

    workflow_ids, source_refs = await load_meeting_refs(db, principal.tenant_id, meeting.id)

    meeting_data = MeetingDTO(
        id=meeting.id,
        client_id=meeting.client_id,
        calendar_event_id=meeting.calendar_event_id,
        event_version=meeting.event_version,
        resolution=MeetingResolution(meeting.resolution),
        title=meeting.title,
        start=meeting.starts_at,
        end=meeting.ends_at,
        workflow_ids=workflow_ids,
        row_version=meeting.row_version,
        source_refs=source_refs,
    )

    await db.commit()

    return Envelope(
        data={"meeting": meeting_data},
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=principal.session_expires_at,
        ),
    )
