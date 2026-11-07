"""Product search, interpretation, comparison and suitability assessment schemas.

Architecture §6.7 API-056 through API-062.
"""
from datetime import datetime, UTC
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import (
    ArtifactRef,
    ConfigRef,
    CatalogRef,
    EvidenceRef,
    Availability,
    Environment,
    Source,
    Reason,
    Blocker,
    Hash,
    Money,
    FieldValue,
)


# Product reference
class ProductRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    id: str
    version: str


# Product filters
FilterOperator = Literal["EQ", "IN", "GTE", "LTE"]
FilterSource = Literal["QUERY", "RM_EDIT", "AUTHORITATIVE"]


class ProductFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    key: str
    operator: FilterOperator
    value: FieldValue
    metric_key: str | None = None
    unit: str | None = None
    source: FilterSource
    hard: bool
    confirmed: bool
    catalog_ref: CatalogRef


# Product metrics
class ProductMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    key: str
    name: str
    value: FieldValue | None
    unit: str | None = None
    definition_ref: ConfigRef
    source: Source


# Product details
class Product(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    ref: ProductRef
    name: str
    asset_class: str
    currencies: list[str]
    risk_code: str | None = None
    minimum_investment: Money | None = None
    fees: list[ProductMetric]
    liquidity: list[ProductMetric]
    metrics: list[ProductMetric]
    esg: list[ProductMetric]
    terms_source: Source
    availability: Availability


# API-056: Interpret query
class ProductInterpretationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    query: str


class ProductInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    query: str
    filters: list[ProductFilter]
    sort_key: str | None = None
    universe_ref: ConfigRef
    profile_ref: str | None = None
    ambiguities: list[str]


class ProductInterpretationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    artifact: "Artifact"


# API-057: Edit filters
class EditFiltersRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    filters: list[ProductFilter]
    sort_key: str | None = None
    confirmation: bool = Field(..., description="Must be true")


# API-058: Search products
class ProductSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    interpretation_ref: ArtifactRef
    confirmation: bool = Field(..., description="Must be true")


class ProductSearch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    interpretation_ref: ArtifactRef
    executed_filters: list[ProductFilter]
    executed_at: datetime
    products: list[Product]
    next_cursor: str | None = None
    no_result_explanation: str | None = None
    soft_edit_suggestions: list[str]
    sources: list[Source]


class ProductSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    artifact: "Artifact"


# API-059: Compare products
class ProductComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    search_ref: ArtifactRef
    product_refs: list[ProductRef]


class ProductComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    search_ref: ArtifactRef
    products: list[Product]
    metric_keys: list[str]


class ProductComparisonResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    artifact: "Artifact"


# API-060: Select candidate
class CandidateSelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    search_ref: ArtifactRef
    product_ref: ProductRef
    confirmation: bool = Field(..., description="Must be true")


class CandidateSelectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    selection_id: UUID
    selected_at: datetime


# API-061: Assess suitability
ProfileValidity = Literal["CURRENT", "EXPIRED", "MISSING", "CONFLICT"]
SuitabilityRating = Literal["GREEN", "YELLOW", "RED", "UNAVAILABLE"]
FactorClassification = Literal["HARD", "SOFT", "UNKNOWN"]
FactorResult = Literal["PASS", "WARN", "FAIL", "MISSING"]


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    product_ref: ProductRef
    account_ref: str | None = None
    amount: Money | None = None
    previous_ref: ArtifactRef | None = None


class SuitabilityFactor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    key: str
    label: str
    classification: FactorClassification
    result: FactorResult
    evidence_refs: list[EvidenceRef]
    explanation: str
    override_permitted: bool


class Assessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    client_id: UUID
    product_ref: ProductRef
    account_ref: str | None = None
    amount: Money | None = None
    profile_id: str | None = None
    profile_version: str | None = None
    profile_validity: ProfileValidity
    input_hash: str = Field(min_length=64, max_length=64)  # SHA-256 hash
    policy_ref: ConfigRef
    rating: SuitabilityRating
    current: bool
    factors: list[SuitabilityFactor]
    ticket_eligible: bool
    blockers: list[Blocker]
    assessed_at: datetime


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    artifact: "Artifact"


# API-062: Override assessment
class SuitabilityOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    assessment_ref: ArtifactRef
    factor_keys: list[str]
    reason: Reason
    rationale: str
    confirmation: bool = Field(..., description="Must be true")


class SuitabilityOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    id: UUID
    assessment_ref: ArtifactRef
    factor_keys: list[str]
    reason: Reason
    rationale: str
    policy_ref: ConfigRef
    actor: str
    at: datetime
    original_rating: Literal["GREEN", "YELLOW", "RED"]


class SuitabilityOverrideResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    override: SuitabilityOverride


# Artifact wrapper for product artifacts
class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    ref: ArtifactRef
    kind: Literal["PRODUCT_INTERPRETATION", "PRODUCT_SEARCH", "PRODUCT_COMPARISON", "ASSESSMENT"]
    payload: ProductInterpretation | ProductSearch | ProductComparison | Assessment
    environment: Environment
    created_at: datetime
