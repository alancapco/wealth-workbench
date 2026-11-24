"""Client memory and conversation DTOs (API-013 / API-014)."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MemoryEntryType = Literal["PREFERENCE", "FACT", "CONSTRAINT", "GOAL"]
MemoryState = Literal["NEEDS_REVIEW", "CONFIRMED", "REJECTED"]


class MemoryProposalCreate(BaseModel):
    """Body of POST /clients/{client_id}/memory/proposals."""

    model_config = ConfigDict(extra="forbid")

    kind: MemoryEntryType
    content: str = Field(min_length=1, max_length=2000)
    source_ref: str = Field(min_length=1, max_length=200)


class MemoryRecordRead(BaseModel):
    """A confirmed memory fact or a pending proposal."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    client_id: UUID
    entry_type: str
    content: str
    source_ref: str
    state: str
    confidence: str | None
    proposed_by: str | None
    proposed_at: datetime
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime


class ConversationRead(BaseModel):
    """A client interaction / conversation note."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    client_id: UUID | None
    interaction_date: datetime
    interaction_type: str | None
    summary: str | None
    preferences_extracted: list | None
    action_items: list | None
    recording_consent: bool | None
    source_kind: str | None
    confidence: float | None
