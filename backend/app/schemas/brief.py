"""Brief domain DTOs per Architecture §6.3."""
from datetime import datetime, UTC
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import (
    ArtifactRef,
    Availability,
    Blocker,
    CapabilityState,
    Completeness,
    Environment,
    EvidenceRef,
    Origin,
    ReviewState,
    Source,
)


class BriefSectionKey(str, Enum):
    """Brief section keys - exactly five required sections."""
    PORTFOLIO_OVERVIEW = "portfolio_overview"
    MATERIAL_CHANGES = "material_changes"
    RECENT_INTERACTIONS = "recent_interactions"
    MARKET_NEWS = "market_news"
    PROPOSED_AGENDA = "proposed_agenda"


# Request DTOs

class GenerateBriefRequest(BaseModel):
    """POST /briefs request per API-004."""
    model_config = ConfigDict(extra="forbid")
    
    workflow_id: UUID
    meeting_id: UUID | None = None
    previous_ref: ArtifactRef | None = None
    section_keys: list[BriefSectionKey]


class SectionReviewItem(BaseModel):
    """Section review item within brief review request."""
    model_config = ConfigDict(extra="forbid")
    
    key: BriefSectionKey
    hash: str = Field(min_length=64, max_length=64)
    decision: str  # APPROVED | REJECTED
    reason: str | None = None


class ReviewBriefRequest(BaseModel):
    """POST /briefs/{brief_id}/reviews request per API-006."""
    model_config = ConfigDict(extra="forbid")
    
    artifact_ref: ArtifactRef
    sections: list[SectionReviewItem]


class SectionEdit(BaseModel):
    """Section edit within brief edit request."""
    model_config = ConfigDict(extra="forbid")
    
    key: BriefSectionKey
    narrative: str
    agenda: list["AgendaItem"] | None = None


class EditBriefRequest(BaseModel):
    """PATCH /briefs/{brief_id} request per API-032."""
    model_config = ConfigDict(extra="forbid")
    
    section_edits: list[SectionEdit]
    reason: str


# Response DTOs

class BriefClaim(BaseModel):
    """Material claim within brief section."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    text: str
    origin: Origin
    evidence_refs: list[EvidenceRef]
    confidence: float | None = Field(None, ge=0, le=1)


class AgendaItem(BaseModel):
    """Agenda item within brief section."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    text: str
    origin: Origin
    evidence_refs: list[EvidenceRef]


class BriefSection(BaseModel):
    """Single section within brief sections per Architecture §6.3."""
    model_config = ConfigDict(extra="forbid")
    
    key: BriefSectionKey
    item_hash: str = Field(min_length=64, max_length=64)
    narrative: str | None = None
    claims: list[BriefClaim] = Field(default_factory=list)
    agenda: list[AgendaItem] = Field(default_factory=list)
    availability: Availability
    completeness: Completeness
    capability_state: CapabilityState
    review_state: ReviewState
    sources: list[Source]
    limitations: list[str] = Field(default_factory=list)


class BriefSections(BaseModel):
    """The five required sections - exact keys."""
    model_config = ConfigDict(extra="forbid")
    
    portfolio_overview: BriefSection
    material_changes: BriefSection
    recent_interactions: BriefSection
    market_news: BriefSection
    proposed_agenda: BriefSection


class BriefHeader(BaseModel):
    """Brief header for list response per API-031."""
    model_config = ConfigDict(extra="forbid")
    
    brief_id: UUID
    artifact_ref: ArtifactRef
    workflow_id: UUID
    meeting_id: UUID | None
    client_id: UUID
    generated_at: datetime
    generated_by: str
    review_state: ReviewState


class Brief(BriefHeader):
    """Complete brief response per API-004/005."""
    model_config = ConfigDict(extra="forbid")
    
    version: int = Field(gt=0)
    environment: Environment
    source_cutoff: datetime | None
    sections: BriefSections
    blockers: list[Blocker] = Field(default_factory=list)


# Response data wrappers

class GenerateBriefData(BaseModel):
    """Response data for POST /briefs."""
    model_config = ConfigDict(extra="forbid")
    
    brief: Brief


class GetBriefData(BaseModel):
    """Response data for GET /briefs/{brief_id}."""
    model_config = ConfigDict(extra="forbid")
    
    brief: Brief


class BriefListData(BaseModel):
    """Response data for GET /workflows/{w}/briefs."""
    model_config = ConfigDict(extra="forbid")
    
    items: list[BriefHeader]
    next_cursor: str | None = None


class ReviewBriefData(BaseModel):
    """Response data for POST /briefs/{brief_id}/reviews."""
    model_config = ConfigDict(extra="forbid")
    
    brief: Brief
    reviews: list[dict]  # Review objects


class EditBriefData(BaseModel):
    """Response data for PATCH /briefs/{brief_id}."""
    model_config = ConfigDict(extra="forbid")
    
    brief: Brief
