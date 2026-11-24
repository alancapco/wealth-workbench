"""Product search, selection, assessment and override models."""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.database import Base


class CandidateSelection(Base):
    """Records M-08 telemetry for product selection without trade intent."""
    __tablename__ = "candidate_selections"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    workflow_id = Column(PGUUID(as_uuid=True), nullable=False)
    search_revision_id = Column(PGUUID(as_uuid=True), nullable=False)
    product_id = Column(Text, nullable=False)
    product_version = Column(Text, nullable=False)
    selected_by = Column(Text, nullable=False)
    selected_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "workflow_id"],
            ["workflows.tenant_id", "workflows.client_id", "workflows.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "search_revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        Index("ix_candidate_selection_workflow", "tenant_id", "client_id", "workflow_id", "selected_at"),
    )


class SuitabilityOverride(Base):
    """Records RM override of soft suitability factors with justification."""
    __tablename__ = "suitability_overrides"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    assessment_revision_id = Column(PGUUID(as_uuid=True), nullable=False)
    factor_keys = Column(Text, nullable=False)  # JSONB array
    reason_code = Column(Text, nullable=False)
    reason_catalog_ref = Column(Text, nullable=False)  # JSONB ConfigRef
    reason_other_text = Column(Text)
    rationale = Column(Text, nullable=False)
    policy_configuration_id = Column(PGUUID(as_uuid=True), nullable=False)
    policy_configuration_revision = Column(Integer, nullable=False)
    actor = Column(Text, nullable=False)
    overridden_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    original_rating = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "assessment_revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "policy_configuration_id"],
            ["configuration_revisions.tenant_id", "configuration_revisions.id"]
        ),
        Index("ix_suitability_override_assessment", "tenant_id", "client_id", "assessment_revision_id"),
        CheckConstraint("original_rating IN ('GREEN','YELLOW','RED')"),
        CheckConstraint("policy_configuration_revision > 0"),
    )
