"""Client context and portfolio DTOs per Architecture §6.1."""
from datetime import date, datetime, UTC
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import (
    CatalogRef,
    ConfigRef,
    EvidenceRef,
    MappedValue,
    Money,
    Source,
)


class ContactChannel(str, Enum):
    """Contact channel enumeration."""
    EMAIL = "EMAIL"
    SMS = "SMS"


class ProfileValidity(str, Enum):
    """Profile validity state per Architecture §6.1."""
    CURRENT = "CURRENT"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"


class AccountEligibility(str, Enum):
    """Account eligibility state per Architecture §6.1."""
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    UNKNOWN = "UNKNOWN"


# Client DTOs

class ClientSummary(BaseModel):
    """Client summary per Architecture §6.1 API-002."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    external_id: str | None
    name: str
    book_id: str
    client_type: str | None
    risk_label: str | None
    source: Source


class Contact(BaseModel):
    """Client contact per Architecture §6.1."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    channel: ContactChannel
    destination: str
    source: Source


class Account(BaseModel):
    """Client account per Architecture §6.1."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    client_id: UUID
    currency: str
    eligibility: AccountEligibility
    source: Source


class Profile(BaseModel):
    """Client profile per Architecture §6.1."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    version: str
    risk_code: str | None
    validity: ProfileValidity
    as_of: datetime | None
    fields: list[MappedValue]
    source: Source


class ContactPolicy(BaseModel):
    """Contact policy per Architecture §6.1."""
    model_config = ConfigDict(extra="forbid")
    
    dnc: bool | None
    channels: list[dict]  # {channel: ContactChannel, consented: bool | None}
    config_ref: ConfigRef | None


class MemoryEntry(BaseModel):
    """Memory entry per Architecture §6.5."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    key: str
    value: dict  # FieldValue
    version: int = Field(gt=0)
    state: str  # CONFIRMED | CONFLICT | SUPERSEDED
    source_ref: dict  # ArtifactRef
    confirmed_by: str
    confirmed_at: datetime
    sources: list[Source]


class ClientDetail(BaseModel):
    """Client detail per Architecture §6.1 API-003."""
    model_config = ConfigDict(extra="forbid")
    
    summary: ClientSummary
    contacts: list[Contact]
    accounts: list[Account]
    profile: Profile | None
    contact_policy: ContactPolicy
    memory: list[MemoryEntry]


# Portfolio DTOs

class Holding(BaseModel):
    """Holding per Architecture §6.1."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    account_id: str | None
    instrument_id: str
    symbol: str | None
    quantity: Decimal | None
    market_value: Money | None
    cost_basis: Money | None
    asset_class: str | None
    source: Source


class Allocation(BaseModel):
    """Allocation per Architecture §6.1."""
    model_config = ConfigDict(extra="forbid")
    
    asset_class: str
    value: Money | None
    weight: Decimal | None
    evidence_refs: list[EvidenceRef]


class PerformancePoint(BaseModel):
    """Performance point per Architecture §6.1."""
    model_config = ConfigDict(extra="forbid")
    
    date: date
    metric_key: str
    value: Decimal | None
    unit: str
    evidence_refs: list[EvidenceRef]


class Portfolio(BaseModel):
    """Portfolio per Architecture §6.1 API-020."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    client_id: UUID
    as_of: datetime | None
    base_currency: str | None
    aum: Money | None
    holdings: list[Holding]
    allocation: list[Allocation]
    performance: list[PerformancePoint]
    sources: list[Source]


# List response wrappers

class ClientListData(BaseModel):
    """Client list response data."""
    model_config = ConfigDict(extra="forbid")
    
    items: list[ClientSummary]
    next_cursor: str | None = None
