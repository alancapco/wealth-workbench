"""Artifact lineage and revision models."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ArtifactLineage(Base):
    __tablename__ = "artifact_lineages"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    workflow_id = Column(PGUUID(as_uuid=True), nullable=False)
    meeting_id = Column(PGUUID(as_uuid=True))
    kind = Column(Text, nullable=False)
    current_revision_id = Column(PGUUID(as_uuid=True))
    created_by = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "workflow_id"],
            ["workflows.tenant_id", "workflows.client_id", "workflows.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "meeting_id"],
            ["meetings.tenant_id", "meetings.client_id", "meetings.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "workflow_id", "meeting_id"],
            ["workflows.tenant_id", "workflows.client_id", "workflows.id", "workflows.meeting_id"]
        ),
        Index("ix_artifact_client_kind", "tenant_id", "client_id", "kind", "created_at"),
        CheckConstraint("kind IN ('BRIEF','TRANSCRIPT','EXTRACTION','NOTES','CRM_CHANGE','TASK','MEMORY_PROPOSAL','MESSAGE','TICKET_PREFILL','PRODUCT_INTERPRETATION','PRODUCT_SEARCH','PRODUCT_COMPARISON','ASSESSMENT','SHARIAH_SCREEN','SHARIAH_ESTIMATE','SHARIAH_PACK','STRUCTURE_PROPOSAL','CONSOLIDATION','ATTENDEE_PACK','FAMILY_SCENARIO','CAPITAL_NOTICE','LIQUIDITY_FORECAST')"),
    )


class ArtifactRevision(Base):
    __tablename__ = "artifact_revisions"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    artifact_id = Column(PGUUID(as_uuid=True), nullable=False)
    version = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    payload = Column(Text, nullable=False)  # JSONB
    environment_kind = Column(Text, nullable=False)
    environment_id = Column(Text, nullable=False)
    created_by = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        UniqueConstraint("tenant_id", "client_id", "artifact_id", "id"),
        UniqueConstraint("tenant_id", "artifact_id", "version"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "artifact_id"],
            ["artifact_lineages.tenant_id", "artifact_lineages.client_id", "artifact_lineages.id"]
        ),
        CheckConstraint("version > 0"),
        CheckConstraint("environment_kind IN ('FIXTURE','INSTITUTION_TEST','PRODUCTION')"),
    )


class ArtifactItem(Base):
    __tablename__ = "artifact_items"

    tenant_id = Column(Text, primary_key=True)
    client_id = Column(PGUUID(as_uuid=True), primary_key=True)
    revision_id = Column(PGUUID(as_uuid=True), primary_key=True)
    item_key = Column(Text, primary_key=True)
    item_hash = Column(String(64), nullable=False)
    status = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "revision_id", "item_key", "item_hash"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        CheckConstraint("status IN ('UNREVIEWED','NEEDS_REVIEW','APPROVED','REJECTED','BLOCKED')"),
    )


class ArtifactDependency(Base):
    __tablename__ = "artifact_dependencies"

    tenant_id = Column(Text, primary_key=True)
    client_id = Column(PGUUID(as_uuid=True), primary_key=True)
    dependent_revision_id = Column(PGUUID(as_uuid=True), primary_key=True)
    basis_revision_id = Column(PGUUID(as_uuid=True), primary_key=True)
    basis_hash = Column(String(64), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "dependent_revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "basis_revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        CheckConstraint("dependent_revision_id <> basis_revision_id"),
    )


class StageArtifactRef(Base):
    __tablename__ = "stage_artifact_refs"

    tenant_id = Column(Text, primary_key=True)
    client_id = Column(PGUUID(as_uuid=True), primary_key=True)
    run_id = Column(PGUUID(as_uuid=True), primary_key=True)
    revision_id = Column(PGUUID(as_uuid=True), primary_key=True)
    direction = Column(Text, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "run_id"],
            ["stage_runs.tenant_id", "stage_runs.client_id", "stage_runs.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        CheckConstraint("direction IN ('INPUT','OUTPUT')"),
    )


class SourceEvidence(Base):
    __tablename__ = "source_evidence"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    environment_kind = Column(Text, nullable=False)
    environment_id = Column(Text, nullable=False)
    availability = Column(Text, nullable=False)
    origin = Column(Text, nullable=False)
    system_key = Column(Text)
    record_id = Column(Text)
    record_version = Column(Text)
    source_as_of = Column(DateTime(timezone=True))
    retrieved_at = Column(DateTime(timezone=True))
    authoritative_owner = Column(Text)
    freshness_configuration_id = Column(PGUUID(as_uuid=True))
    live_response = Column(Boolean, nullable=False, default=False)
    adapter_receipt_id = Column(Text)
    confidence = Column(Text)  # Numeric
    evidence_location = Column(Text)  # JSONB
    limitations = Column(Text, nullable=False, default='[]')  # JSONB

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["client_scope.tenant_id", "client_scope.client_id"]
        ),
        CheckConstraint("environment_kind IN ('FIXTURE','INSTITUTION_TEST','PRODUCTION')"),
        CheckConstraint("availability IN ('AVAILABLE','STALE','UNAVAILABLE','CONFLICT')"),
        CheckConstraint("origin IN ('RECORDED','DERIVED','RM_ENTERED')"),
        CheckConstraint("NOT live_response OR (environment_kind <> 'FIXTURE' AND adapter_receipt_id IS NOT NULL AND system_key IS NOT NULL AND record_id IS NOT NULL AND retrieved_at IS NOT NULL)"),
    )


class RevisionSource(Base):
    __tablename__ = "revision_sources"

    tenant_id = Column(Text, primary_key=True)
    client_id = Column(PGUUID(as_uuid=True), primary_key=True)
    revision_id = Column(PGUUID(as_uuid=True), primary_key=True)
    source_id = Column(PGUUID(as_uuid=True), primary_key=True)
    claim_path = Column(Text, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "source_id"],
            ["source_evidence.tenant_id", "source_evidence.client_id", "source_evidence.id"]
        ),
    )


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    revision_id = Column(PGUUID(as_uuid=True), nullable=False)
    scope = Column(Text, nullable=False)
    item_key = Column(Text)
    item_hash = Column(String(64), nullable=False)
    decision = Column(Text, nullable=False)
    actor = Column(Text, nullable=False)
    reason = Column(Text)  # JSONB
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "revision_id", "item_key", "item_hash"],
            ["artifact_items.tenant_id", "artifact_items.client_id", "artifact_items.revision_id", "artifact_items.item_key", "artifact_items.item_hash"]
        ),
        Index("ix_review_revision", "tenant_id", "client_id", "revision_id", "recorded_at"),
        CheckConstraint("scope IN ('ARTIFACT','ITEM')"),
        CheckConstraint("decision IN ('APPROVED','REJECTED')"),
        CheckConstraint("(scope = 'ARTIFACT' AND item_key IS NULL) OR (scope = 'ITEM' AND item_key IS NOT NULL)"),
    )
