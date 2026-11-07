"""Action preview, authorization, and execution schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import (
    ArtifactRef,
    ConfigRef,
    EvidenceRef,
    ItemRef,
    Environment,
    Blocker,
    Hash,
)


# Action classes
ActionClass = Literal["CRM_WRITE", "TASK_WRITE", "MEMORY_WRITE", "CLIENT_SEND", "TICKET_PREFILL"]
ActionStatus = Literal["PENDING", "SENDING", "SUCCEEDED", "FAILED_SAFE", "UNKNOWN", "RECONCILE_REQUIRED", "CANCELED_BEFORE_DISPATCH"]
ProviderState = Literal["ACCEPTED", "SCHEDULED", "DELIVERED", "WRITTEN", "PREFILLED", "NOT_ACCEPTED", "UNKNOWN"]
AttemptMode = Literal["DISPATCH", "READBACK"]
AttemptStatus = Literal["STARTED", "CONFIRMED", "NOT_ACCEPTED", "UNKNOWN"]


# Request payloads (simplified for isolated testing - full types would be in domain schemas)
class ActionRequest(BaseModel):
    """Base action request - discriminated by action_class."""
    model_config = ConfigDict(extra="forbid")


# API-048: Create preview
class CreateActionPreviewRequest(BaseModel):
    artifact_ref: ArtifactRef
    action_class: ActionClass
    model_config = ConfigDict(extra="forbid")


class ActionPreviewResponse(BaseModel):
    id: UUID
    artifact_ref: ArtifactRef
    action_class: ActionClass
    preview_hash: Hash
    environment: Environment
    provider_key: str
    destination_ref: str
    context_revision: int
    created_at: datetime
    blockers: list[Blocker] = Field(default_factory=list)
    model_config = ConfigDict(extra="forbid")


# API-049: Authorize preview
class AuthorizePreviewRequest(BaseModel):
    preview_hash: Hash
    confirmation: bool = Field(..., description="Must be true")
    model_config = ConfigDict(extra="forbid")


class AuthorizationState(BaseModel):
    state: Literal["VALID", "INVALIDATED", "REVOKED"]
    invalidated_at: datetime | None = None
    invalidation_code: str | None = None


class ActionAuthorizationResponse(BaseModel):
    id: UUID
    preview_id: UUID
    preview_hash: Hash
    action_class: ActionClass
    actor: str
    authorized_at: datetime
    state: Literal["VALID", "INVALIDATED", "REVOKED"]
    model_config = ConfigDict(extra="forbid")


# API-011: Execute action
class ExecuteActionRequest(BaseModel):
    """Execute action - only authorization_id, no payload substitution."""
    authorization_id: UUID
    model_config = ConfigDict(extra="forbid")


class AttemptSummary(BaseModel):
    id: UUID
    number: int
    mode: AttemptMode
    status: AttemptStatus
    started_at: datetime
    ended_at: datetime | None
    error_code: str | None
    receipt_ref: str | None
    model_config = ConfigDict(extra="forbid")


class ActionResponse(BaseModel):
    id: UUID
    authorization_id: UUID
    action_class: ActionClass
    status: ActionStatus
    provider_ref: str | None
    provider_state: ProviderState | None
    created_at: datetime
    submitted_at: datetime | None
    confirmed_at: datetime | None
    readback_at: datetime | None
    error_code: str | None
    can_reconcile: bool
    can_retry: bool
    attempts: list[AttemptSummary]
    model_config = ConfigDict(extra="forbid")


# API-050: Reconcile action
class ReconcileActionRequest(BaseModel):
    """Trigger readback reconciliation."""
    model_config = ConfigDict(extra="forbid")


# API-051: Retry action
class RetryActionRequest(BaseModel):
    confirmation: bool = Field(..., description="Must be true")
    model_config = ConfigDict(extra="forbid")
