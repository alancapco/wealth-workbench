"""Message artifact and generation schemas per architecture §6.5."""
from datetime import datetime, UTC
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import (
    ConfigRef,
    EvidenceRef,
    ItemRef,
    Origin,
)


# Message generation modes and channels
MessageMode = Literal["FOLLOWUP", "OUTREACH"]
MessageChannel = Literal["EMAIL", "SMS", "WHATSAPP"]


# Priority reason reference (from §6.6)
class PriorityReasonRef(BaseModel):
    """Reference to a specific priority reason from evaluation."""
    model_config = ConfigDict(extra="forbid")
    
    evaluation_id: UUID
    client_id: UUID
    reason_key: str
    reason_hash: str = Field(min_length=64, max_length=64)


# Message generation request (API-052)
class MessageGenerate(BaseModel):
    """Request to generate message from accepted items or priority reason."""
    model_config = ConfigDict(extra="forbid")
    
    mode: MessageMode
    channel: MessageChannel
    template_ref: ConfigRef
    accepted_item_refs: list[ItemRef] = Field(default_factory=list)
    priority_reason_ref: PriorityReasonRef | None = None


# Message recipient
class MessageRecipient(BaseModel):
    """Message recipient with confirmation state."""
    model_config = ConfigDict(extra="forbid")
    
    contact_id: str
    destination: str
    confirmed: bool


# Message disclosure
class MessageDisclosure(BaseModel):
    """Mandatory disclosure with reference."""
    model_config = ConfigDict(extra="forbid")
    
    ref: ConfigRef
    text: str


# Message claim with evidence
class MessageClaim(BaseModel):
    """Grounded claim with evidence and origin."""
    model_config = ConfigDict(extra="forbid")
    
    text: str
    evidence_refs: list[EvidenceRef]
    origin: Origin


# Message artifact payload (stored in artifact_revisions.payload)
class Message(BaseModel):
    """Complete message artifact with grounded content."""
    model_config = ConfigDict(extra="forbid")
    
    mode: MessageMode
    channel: MessageChannel
    template_ref: ConfigRef
    recipients: list[MessageRecipient]
    subject: str | None = None
    body: str
    disclosures: list[MessageDisclosure]
    basis_refs: list[ItemRef]
    priority_reason_ref: PriorityReasonRef | None = None
    claims: list[MessageClaim]


# API responses
class MessageArtifactResponse(BaseModel):
    """Response containing message artifact."""
    model_config = ConfigDict(extra="forbid")
    
    artifact_id: UUID
    revision_id: UUID
    version: int
    message: Message
    created_at: datetime
    created_by: str


# Message edit request (PATCH /artifacts/{id})
class MessageEdit(BaseModel):
    """Editable message fields for artifact PATCH."""
    model_config = ConfigDict(extra="forbid")
    
    recipients: list[MessageRecipient] | None = None
    subject: str | None = None
    body: str | None = None
    # Template and claims are not editable - require regeneration
