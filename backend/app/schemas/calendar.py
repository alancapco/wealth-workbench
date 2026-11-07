"""Calendar and meeting DTOs per Architecture §6.1."""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.client import ClientSummary
from app.schemas.common import CapabilityState, EvidenceRef, Source


class CalendarEventStatus(str, Enum):
    """Calendar event status per Architecture §6.1."""
    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"
    INELIGIBLE = "INELIGIBLE"


class MatchState(str, Enum):
    """Calendar event match state per Architecture §6.1."""
    VERIFIED = "VERIFIED"
    AMBIGUOUS = "AMBIGUOUS"
    UNMATCHED = "UNMATCHED"
    CONFLICT = "CONFLICT"


class MeetingResolution(str, Enum):
    """Meeting resolution per Architecture §6.1."""
    VERIFIED = "VERIFIED"
    RM_CONFIRMED = "RM_CONFIRMED"
    CONFLICT = "CONFLICT"


# Request DTOs

class EventResolutionRequest(BaseModel):
    """Event resolution request per API-023."""
    model_config = ConfigDict(extra="forbid")
    
    event_version: str
    client_id: UUID
    confirmation: bool


# Response DTOs

class CalendarEvent(BaseModel):
    """Calendar event per Architecture §6.1 API-022."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    provider_event_id: str
    provider_version: str
    title: str
    start: datetime
    end: datetime
    status: CalendarEventStatus
    attendee_hints: list[str]
    match_state: MatchState
    candidates: list[ClientSummary]
    resolved_meeting_id: UUID | None
    source: Source


class Meeting(BaseModel):
    """Meeting per Architecture §6.1 API-024."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    client_id: UUID
    calendar_event_id: UUID | None
    event_version: str | None
    resolution: MeetingResolution
    title: str | None
    start: datetime | None
    end: datetime | None
    workflow_ids: list[UUID]
    row_version: int = Field(gt=0)
    source_refs: list[EvidenceRef]


# List response wrappers

class CalendarEventListData(BaseModel):
    """Calendar event list response data per API-022."""
    model_config = ConfigDict(extra="forbid")
    
    items: list[CalendarEvent]
    next_cursor: str | None = None
    capability_state: CapabilityState
