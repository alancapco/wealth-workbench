"""Common DTO contracts - frozen response envelope, provenance, scope, and shared types.

Architecture §3.2, §3.3, §5 - authoritative definitions.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Response envelope
T = TypeVar("T")


class ResponseMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    request_id: UUID
    served_at: datetime
    next_cursor: str | None = None


class Envelope(BaseModel, Generic[T]):
    """Success response envelope with data + meta."""
    model_config = ConfigDict(extra="forbid")
    
    data: T
    meta: ResponseMeta


# Provenance dimensions - independent, never one overloaded enum
class EnvironmentKind(str, Enum):
    FIXTURE = "FIXTURE"
    INSTITUTION_TEST = "INSTITUTION_TEST"
    PRODUCTION = "PRODUCTION"


class Environment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    kind: EnvironmentKind
    id: str


class Availability(str, Enum):
    AVAILABLE = "AVAILABLE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    CONFLICT = "CONFLICT"


class Origin(str, Enum):
    RECORDED = "RECORDED"
    DERIVED = "DERIVED"
    RM_ENTERED = "RM_ENTERED"


class Source(BaseModel):
    """Independent provenance dimensions per architecture §3.2."""
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    environment: Environment
    availability: Availability
    origin: Origin
    system_key: str | None = None
    record_id: str | None = None
    record_version: str | None = None
    as_of: datetime | None = None
    retrieved_at: datetime | None = None
    authoritative_owner: str | None = None
    freshness_policy_ref: "ConfigRef | None" = None
    live_response: bool
    adapter_receipt_id: str | None = None
    confidence: Decimal | None = None
    evidence: "EvidenceLocation | None" = None
    limitation_codes: list[str] = Field(default_factory=list)


class EvidenceLocationKind(str, Enum):
    RECORD = "RECORD"
    TRANSCRIPT = "TRANSCRIPT"
    DOCUMENT = "DOCUMENT"
    RM_ENTRY = "RM_ENTRY"


class EvidenceLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    kind: EvidenceLocationKind
    record_uri: str | None = None
    segment_id: UUID | None = None
    document_ref: str | None = None
    page: int | None = Field(None, gt=0)
    excerpt: str | None = None
    entered_by: str | None = None


class Completeness(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    EMPTY = "EMPTY"


class CapabilityState(str, Enum):
    READY = "READY"
    UNCONFIGURED = "UNCONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"


class Region(BaseModel, Generic[T]):
    """Region wraps value with availability/capability state."""
    model_config = ConfigDict(extra="forbid")
    
    availability: Availability
    completeness: Completeness
    capability_state: CapabilityState
    as_of: datetime | None
    value: T
    sources: list[Source]
    error_code: str | None = None


# Scope and configuration
class Scope(BaseModel):
    """Tenant/book/jurisdiction scope per architecture §3.3."""
    model_config = ConfigDict(extra="forbid")
    
    tenant_id: str
    book_id: str | None = None
    jurisdiction: str | None = None


class ConfigRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    revision: int = Field(gt=0)
    hash: str = Field(min_length=64, max_length=64)
    
    @field_validator("hash")
    @classmethod
    def validate_hash_hex(cls, v: str) -> str:
        # Validate after length check from Field
        if len(v) != 64:
            raise ValueError("Hash must be exactly 64 characters")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("Hash must be lowercase hex characters")
        return v


class CatalogRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    config_ref: ConfigRef
    catalog_key: str


class Reason(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    code: str
    catalog_ref: CatalogRef
    other_text: str | None = None


# Common scalar types
class Money(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)
    
    @field_validator("amount")
    @classmethod
    def validate_finite(cls, v: Decimal) -> Decimal:
        if not v.is_finite():
            raise ValueError("Amount must be finite")
        return v


class Hash(str):
    """64 lowercase hex SHA-256 hash."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Hash must be a string")
        if len(v) != 64:
            raise ValueError("Hash must be 64 characters")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("Hash must be lowercase hex")
        return v


# Field value types for catalog-validated extensibility
class FieldValueType(str, Enum):
    TEXT = "TEXT"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"
    REFERENCE = "REFERENCE"
    CHOICE = "CHOICE"
    CHOICE_LIST = "CHOICE_LIST"
    NULL = "NULL"


class FieldValue(BaseModel):
    """Catalog-validated extensibility for approved provider fields."""
    model_config = ConfigDict(extra="forbid")
    
    type: FieldValueType
    value: str | Decimal | bool | date | datetime | list[str] | None


class MappedValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    field_key: str
    value: FieldValue
    catalog_ref: CatalogRef


# Artifact references
class ArtifactRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    artifact_id: UUID
    revision_id: UUID
    version: int = Field(gt=0)
    hash: str = Field(min_length=64, max_length=64)


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    source_id: UUID
    source_version: str | None = None


class ItemRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    artifact_ref: ArtifactRef
    item_key: str
    item_hash: str = Field(min_length=64, max_length=64)


# Review types
class ReviewScope(str, Enum):
    ITEM = "ITEM"
    ARTIFACT = "ARTIFACT"


class ReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewState(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    scope: ReviewScope
    item_key: str | None = None
    item_hash: str = Field(min_length=64, max_length=64)
    decision: ReviewDecision
    actor: str
    at: datetime
    reason: Reason | None = None


class ReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    key: str
    hash: str = Field(min_length=64, max_length=64)
    review_state: ReviewState
    evidence_refs: list[EvidenceRef]


class BlockerResolution(str, Enum):
    SAFE_RETRY = "SAFE_RETRY"
    EDIT = "EDIT"
    REVIEW = "REVIEW"
    ADMIN = "ADMIN"
    CHECK_STATUS = "CHECK_STATUS"
    NONE = "NONE"


class Blocker(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    code: str
    field: str | None = None
    config_ref: ConfigRef | None = None
    resolution: BlockerResolution


class Capability(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    key: str
    state: CapabilityState
    blockers: list[Blocker]
