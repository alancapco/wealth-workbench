"""Workflow orchestration DTOs per Architecture §6.2."""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ArtifactRef, Blocker, ConfigRef


class WorkflowType(str, Enum):
    """Workflow type enumeration per Architecture §6.2."""
    MEETING_PREP = "MEETING_PREP"
    MEETING_FOLLOWUP = "MEETING_FOLLOWUP"
    OUTREACH = "OUTREACH"
    PRODUCT_SEARCH = "PRODUCT_SEARCH"
    SHARIAH_REVIEW = "SHARIAH_REVIEW"
    HOUSEHOLD_REVIEW = "HOUSEHOLD_REVIEW"


class WorkflowStatus(str, Enum):
    """Workflow status enumeration per Architecture §6.2."""
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"
    COMPLETED = "COMPLETED"


class StageStatus(str, Enum):
    """Stage status enumeration per Architecture §6.2."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    COMPLETED = "COMPLETED"


class WorkflowEntry(str, Enum):
    """Workflow entry point enumeration."""
    MY_DAY = "MY_DAY"
    CALENDAR = "CALENDAR"
    CLIENT = "CLIENT"
    PRIORITY = "PRIORITY"


# Request DTOs

class MeetingCreate(BaseModel):
    """Manual meeting creation fields per Architecture §6.1."""
    model_config = ConfigDict(extra="forbid")
    
    calendar_event_id: None = None
    title: str | None = None
    start: datetime | None = None
    end: datetime | None = None


class StartWorkflow(BaseModel):
    """Start workflow request per API-007."""
    model_config = ConfigDict(extra="forbid")
    
    type: WorkflowType
    client_id: UUID
    meeting_id: UUID | None = None
    meeting: MeetingCreate | None = None
    entry: WorkflowEntry
    resume_workflow_id: UUID | None = None
    task_context: str | None = None


class RunStageRequest(BaseModel):
    """Stage run request per API-009."""
    model_config = ConfigDict(extra="forbid")
    
    input_refs: list[ArtifactRef]
    context_revision: int = Field(gt=0)


class PauseWorkflowRequest(BaseModel):
    """Pause workflow request per API-026."""
    model_config = ConfigDict(extra="forbid")
    
    reason: str | None = None


class ResumeWorkflowRequest(BaseModel):
    """Resume workflow request per API-027 - empty body."""
    model_config = ConfigDict(extra="forbid")


class AbandonWorkflowRequest(BaseModel):
    """Abandon workflow request per API-028."""
    model_config = ConfigDict(extra="forbid")
    
    confirmation: bool
    reason: str | None = None


# Response DTOs

class StageSummary(BaseModel):
    """Stage summary per Architecture §6.2."""
    model_config = ConfigDict(extra="forbid")
    
    key: str
    status: StageStatus
    run_id: UUID | None = None
    skill_id: str
    skill_version: str
    artifact_refs: list[ArtifactRef]
    blockers: list[Blocker]


class Workflow(BaseModel):
    """Workflow response per Architecture §6.2."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    type: WorkflowType
    client_id: UUID
    meeting_id: UUID | None
    status: WorkflowStatus
    row_version: int = Field(gt=0)
    context_revision: int = Field(gt=0)
    entry: str
    current_stage: str | None
    stages: list[StageSummary]
    action_ids: list[UUID]
    last_confirmed_at: datetime
    next_decision: str | None


class StageRun(BaseModel):
    """Stage run response per Architecture §6.2."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    workflow_id: UUID
    stage_key: str
    status: StageStatus
    input_refs: list[ArtifactRef]
    output_refs: list[ArtifactRef]
    context_revision: int = Field(gt=0)
    skill_id: str
    skill_version: str
    started_at: datetime | None
    completed_at: datetime | None
    manual_intervention: bool
    error_code: str | None


class SkillDescriptor(BaseModel):
    """Skill descriptor per Architecture §6.2."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    version: str
    input_kind: list[str]
    output_kind: list[str]
    required_permissions: list[str]
    policy_keys: list[str]
    flag_key: str | None = None
    model_ref: str | None = None
    prompt_ref: ConfigRef | None = None
    deterministic_rule_ref: ConfigRef | None = None
    timeout_policy_ref: ConfigRef | None = None


# List response wrappers

class WorkflowListData(BaseModel):
    """Workflow list response data."""
    model_config = ConfigDict(extra="forbid")
    
    items: list[Workflow]
    next_cursor: str | None = None


class SkillListData(BaseModel):
    """Skill list response data."""
    model_config = ConfigDict(extra="forbid")
    
    items: list[SkillDescriptor]
    next_cursor: str | None = None
