"""Priority ranking DTOs per Architecture §6.6.

API-015/016/053/054/055: book-wide evaluation, reasons, controls, contact outcomes.
"""
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.client import ClientSummary
from app.schemas.common import (
    CapabilityState,
    ConfigRef,
    Environment,
    EvidenceRef,
    FieldValue,
    Reason,
    Source,
)


# Enums

class EvaluationStatus(str, Enum):
    """Priority evaluation status per architecture §6.6."""
    CURRENT = "CURRENT"
    STALE = "STALE"
    FAILED = "FAILED"


class ReasonClass(str, Enum):
    """Priority reason class per architecture §6.6."""
    RISK = "RISK"
    OPPORTUNITY = "OPPORTUNITY"
    RETENTION = "RETENTION"


class ControlType(str, Enum):
    """Priority control type per architecture §6.6 API-054."""
    SNOOZE = "SNOOZE"
    DISMISS = "DISMISS"
    PIN = "PIN"


class ContactOutcomeType(str, Enum):
    """Contact outcome type per architecture §6.6 API-055."""
    CONTACTED = "CONTACTED"
    MEETING_BOOKED = "MEETING_BOOKED"
    NO_RESPONSE = "NO_RESPONSE"
    NOT_RELEVANT = "NOT_RELEVANT"


class MeaningfulTouchpoint(str, Enum):
    """Meaningful touchpoint classification per architecture §6.6."""
    CONFIRMED = "CONFIRMED"
    NOT_CONFIRMED = "NOT_CONFIRMED"
    UNCONFIGURED = "UNCONFIGURED"


# DTOs

class PrioritySignal(BaseModel):
    """Signal contributing to priority reason per architecture §6.6."""
    model_config = ConfigDict(extra="forbid")
    
    key: str
    value: FieldValue
    source: Source


class PriorityReason(BaseModel):
    """Priority reason with evidence per architecture §6.6 API-015."""
    model_config = ConfigDict(extra="forbid")
    
    key: str
    hash: str = Field(min_length=64, max_length=64)
    classes: list[ReasonClass]
    code: str
    explanation: str
    signals: list[PrioritySignal]
    evidence_refs: list[EvidenceRef]


class PriorityReasonRef(BaseModel):
    """Reference to priority reason per architecture §6.6 API-055."""
    model_config = ConfigDict(extra="forbid")
    
    evaluation_id: UUID
    client_id: UUID
    reason_key: str
    reason_hash: str = Field(min_length=64, max_length=64)


class PriorityControl(BaseModel):
    """RM control (snooze/dismiss/pin) per architecture §6.6 API-054."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    client_id: UUID
    book_id: str
    request: dict  # Control request variant: {type:SNOOZE,until:Timestamp}|{type:DISMISS,reason:Reason}|{type:PIN,pinned:boolean}
    actor: str
    recorded_at: datetime
    row_version: int = Field(gt=0)
    policy_ref: ConfigRef


class PriorityItem(BaseModel):
    """Priority ranked client per architecture §6.6 API-015."""
    model_config = ConfigDict(extra="forbid")
    
    client: ClientSummary
    rank: int = Field(ge=1, le=10)
    reasons: list[PriorityReason]
    rank_change_explanation: str | None = None
    controls: list[PriorityControl]
    last_updated_at: datetime


class PriorityEvaluation(BaseModel):
    """Book-wide priority evaluation per architecture §6.6 API-015/016."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    book_id: str
    date: date
    timezone: str
    evaluated_at: datetime
    policy_ref: ConfigRef
    status: EvaluationStatus
    criteria_summary: str
    items: list[PriorityItem]
    environment: Environment
    source_refs: list[EvidenceRef]


# Request DTOs

class EvaluatePriorityRequest(BaseModel):
    """Request for priority evaluation per architecture API-015."""
    model_config = ConfigDict(extra="forbid")
    
    date: date
    timezone: str
    trigger: str  # RM_REFRESH | MATERIAL_SIGNAL


class SnoozeControl(BaseModel):
    """Snooze control request per architecture §6.6."""
    model_config = ConfigDict(extra="forbid")
    
    type: str = Field(pattern="^SNOOZE$")
    until: datetime


class DismissControl(BaseModel):
    """Dismiss control request per architecture §6.6."""
    model_config = ConfigDict(extra="forbid")
    
    type: str = Field(pattern="^DISMISS$")
    reason: Reason


class PinControl(BaseModel):
    """Pin control request per architecture §6.6."""
    model_config = ConfigDict(extra="forbid")
    
    type: str = Field(pattern="^PIN$")
    pinned: bool


class PriorityControlRequest(BaseModel):
    """Request to set priority control per architecture API-054."""
    model_config = ConfigDict(extra="forbid")
    
    client_id: UUID
    recommendation_ref: PriorityReasonRef
    control: SnoozeControl | DismissControl | PinControl


class ContactOutcomeRequest(BaseModel):
    """Request to record contact outcome per architecture API-055."""
    model_config = ConfigDict(extra="forbid")
    
    recommendation_ref: PriorityReasonRef
    client_id: UUID
    outcome: ContactOutcomeType
    occurred_at: datetime
    note: str | None = None
    meeting_id: UUID | None = None
    evidence_refs: list[EvidenceRef]


# Response DTOs

class EvaluationData(BaseModel):
    """Priority evaluation response data per architecture API-015."""
    model_config = ConfigDict(extra="forbid")
    
    evaluation: PriorityEvaluation


class EvaluationStatusData(BaseModel):
    """Priority evaluation status response per architecture API-016."""
    model_config = ConfigDict(extra="forbid")
    
    evaluation: PriorityEvaluation | None
    capability_state: CapabilityState


class ControlResponseData(BaseModel):
    """Priority control response per architecture API-054."""
    model_config = ConfigDict(extra="forbid")
    
    control: PriorityControl
    evaluation_state: str  # STALE | CURRENT


class ContactOutcomeResponseData(BaseModel):
    """Contact outcome response per architecture API-055."""
    model_config = ConfigDict(extra="forbid")
    
    outcome_id: UUID
    meaningful_touchpoint: MeaningfulTouchpoint
