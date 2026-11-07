"""Shariah pilot schemas - evidence and estimate DTOs (default OFF, DEC-05 gated).

U-015: Evidence-backed Shariah compliance estimation, NOT fatwa or approval.
Architecture API-075, API-076 (modified for U-015 simplified scope).
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Enums

class EvidenceType(str, Enum):
    """Shariah evidence type from certified bodies."""
    AAOIFI_CERT = "AAOIFI_CERT"
    SSB_REPORT = "SSB_REPORT"
    SCREENING_RESULT = "SCREENING_RESULT"


class ComplianceStatus(str, Enum):
    """Compliance status from evidence source."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    UNCERTAIN = "UNCERTAIN"


class EstimateValue(str, Enum):
    """Shariah compliance estimate - preliminary, not authoritative."""
    LIKELY_COMPLIANT = "LIKELY_COMPLIANT"
    LIKELY_NON_COMPLIANT = "LIKELY_NON_COMPLIANT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


# DTOs

class ShariahEvidenceDetail(BaseModel):
    """Shariah evidence from certified body."""
    model_config = ConfigDict(extra="forbid")

    evidence_type: EvidenceType
    source_url: str
    captured_at: datetime
    expires_at: datetime | None = None
    certification_body: str
    compliance_status: ComplianceStatus


class ShariahEstimateRequest(BaseModel):
    """Request to generate Shariah compliance estimate."""
    model_config = ConfigDict(extra="forbid")

    product_ref: str = Field(min_length=1)


class ShariahEstimateResponse(BaseModel):
    """Shariah compliance estimate response with disclaimer."""
    model_config = ConfigDict(extra="forbid")

    estimate_id: UUID
    product_ref: str
    estimate: EstimateValue
    reasoning: str
    evidence_count: int
    evidence_ids: list[UUID]
    disclaimer: str
    created_at: datetime


class EstimateDisclaimer(BaseModel):
    """Constant disclaimer for Shariah estimates per U-015."""
    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        default=(
            "This is a preliminary technical estimate based on available evidence. "
            "It is NOT a fatwa, religious authority ruling, or compliance approval. "
            "Consult qualified Shariah scholars before making investment decisions."
        )
    )


class ShariahEvidenceListResponse(BaseModel):
    """List of valid evidence for a product."""
    model_config = ConfigDict(extra="forbid")

    product_ref: str
    evidence_count: int
    evidence: list[ShariahEvidenceDetail]
