"""Shariah pilot models - default OFF, DEC-05 gated.

U-015: Evidence-backed Shariah compliance estimation (not fatwa/approval).
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID

from app.core.database import Base


class ShariahEvidence(Base):
    """Shariah compliance evidence from certified bodies.
    
    Architecture §6.10: Evidence-backed screening, not authoritative ruling.
    """
    __tablename__ = "shariah_evidence"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    product_ref = Column(Text, nullable=False)
    evidence_type = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    certification_body = Column(Text, nullable=False)
    compliance_status = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        CheckConstraint(
            "evidence_type IN ('AAOIFI_CERT','SSB_REPORT','SCREENING_RESULT')"
        ),
        CheckConstraint(
            "compliance_status IN ('COMPLIANT','NON_COMPLIANT','UNCERTAIN')"
        ),
    )


class ShariahEstimate(Base):
    """Shariah compliance estimate - preliminary, not fatwa.
    
    Architecture §6.10: Estimate based on evidence, explicit limitations.
    """
    __tablename__ = "shariah_estimates"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    product_ref = Column(Text, nullable=False)
    workflow_id = Column(PGUUID(as_uuid=True), nullable=False)
    estimate = Column(Text, nullable=False)
    evidence_ids = Column(ARRAY(PGUUID(as_uuid=True)), nullable=False)
    reasoning = Column(Text, nullable=False)
    limitations = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        CheckConstraint(
            "estimate IN ('LIKELY_COMPLIANT','LIKELY_NON_COMPLIANT','INSUFFICIENT_DATA')"
        ),
    )
