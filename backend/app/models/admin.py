"""Admin and audit models."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ConfigScope(Base):
    __tablename__ = "config_scopes"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), nullable=False)
    book_id = Column(Text)
    jurisdiction = Column(Text)
    scope_key = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "scope_key"),
        ForeignKeyConstraint(
            ["tenant_id", "book_id"],
            ["books.tenant_id", "books.book_id"]
        ),
        CheckConstraint("scope_key = jsonb_build_array(tenant_id, book_id, jurisdiction)::text"),
    )


class ConfigurationRevision(Base):
    __tablename__ = "configuration_revisions"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    scope_id = Column(PGUUID(as_uuid=True), nullable=False)
    config_key = Column(Text, nullable=False)
    config_class = Column(Text, nullable=False)
    revision = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    status = Column(Text, nullable=False)
    value = Column(Text, nullable=False)  # JSONB
    author = Column(Text, nullable=False)
    change_reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "scope_id", "config_key", "revision"),
        UniqueConstraint("tenant_id", "scope_id", "config_key", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "scope_id"],
            ["config_scopes.tenant_id", "config_scopes.id"]
        ),
        CheckConstraint("config_class IN ('FIELD_MAPPING','RANKING','TEMPLATE','CONSENT','INTEGRATION','GOVERNANCE','METHOD','CATALOG')"),
        CheckConstraint("revision > 0"),
        CheckConstraint("status IN ('UNCONFIGURED','DRAFT','VALIDATED','APPROVED','RETIRED')"),
    )


class GovernanceEvidence(Base):
    __tablename__ = "governance_evidence"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    scope_id = Column(PGUUID(as_uuid=True), nullable=False)
    evidence_key = Column(Text, nullable=False)
    owner = Column(Text, nullable=False)
    environment_kind = Column(Text, nullable=False)
    environment_id = Column(Text, nullable=False)
    reference = Column(Text, nullable=False)
    version = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    approved_by = Column(Text)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "scope_id"],
            ["config_scopes.tenant_id", "config_scopes.id"]
        ),
        CheckConstraint("environment_kind IN ('FIXTURE','INSTITUTION_TEST','PRODUCTION')"),
        CheckConstraint("status IN ('PENDING','APPROVED','EXPIRED','BLOCKED')"),
    )


class ConfigurationApproval(Base):
    __tablename__ = "configuration_approvals"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    configuration_id = Column(PGUUID(as_uuid=True), nullable=False)
    content_hash = Column(String(64), nullable=False)
    actor = Column(Text, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "configuration_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "configuration_id"],
            ["configuration_revisions.tenant_id", "configuration_revisions.id"]
        ),
    )


class CapabilityControl(Base):
    __tablename__ = "capability_controls"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    scope_id = Column(PGUUID(as_uuid=True), nullable=False)
    capability_key = Column(Text, nullable=False)
    enabled = Column(Text, nullable=False, default='false')
    revision = Column(Integer, nullable=False)
    cohort_refs = Column(Text, nullable=False, default='[]')  # JSONB
    reason = Column(Text, nullable=False)
    actor = Column(Text, nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "scope_id", "capability_key", "revision"),
        UniqueConstraint("tenant_id", "scope_id", "capability_key", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "scope_id"],
            ["config_scopes.tenant_id", "config_scopes.id"]
        ),
        CheckConstraint("revision > 0"),
    )


class IdempotencyRequest(Base):
    __tablename__ = "idempotency_requests"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), nullable=False)
    actor = Column(Text, nullable=False)
    method = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    idempotency_key = Column(PGUUID(as_uuid=True), nullable=False)
    request_hash = Column(String(64), nullable=False)
    status = Column(Text, nullable=False)
    response_status = Column(Integer)
    response_body = Column(Text)  # JSONB
    resource_ref = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("tenant_id", "actor", "method", "path", "idempotency_key"),
        CheckConstraint("status IN ('IN_PROGRESS','COMPLETED')"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), nullable=False)
    client_id = Column(PGUUID(as_uuid=True))
    workflow_id = Column(PGUUID(as_uuid=True))
    revision_id = Column(PGUUID(as_uuid=True))
    actor = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    resource_type = Column(Text, nullable=False)
    resource_id = Column(Text, nullable=False)
    correlation_id = Column(PGUUID(as_uuid=True), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    previous_hash = Column(String(64))
    event_hash = Column(String(64), nullable=False)
    safe_details = Column(Text, nullable=False)  # JSONB

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "event_hash"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["client_scope.tenant_id", "client_scope.client_id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "workflow_id"],
            ["workflows.tenant_id", "workflows.client_id", "workflows.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        Index("ix_audit_resource", "tenant_id", "resource_type", "resource_id", "occurred_at"),
        CheckConstraint("(workflow_id IS NULL AND revision_id IS NULL) OR client_id IS NOT NULL"),
    )


class AuditChainHead(Base):
    __tablename__ = "audit_chain_heads"

    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), primary_key=True)
    last_event_id = Column(PGUUID(as_uuid=True), nullable=False)
    last_event_hash = Column(String(64), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "last_event_id"],
            ["audit_events.tenant_id", "audit_events.id"]
        ),
    )


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), nullable=False)
    book_id = Column(Text)
    client_id = Column(PGUUID(as_uuid=True))
    workflow_id = Column(PGUUID(as_uuid=True))
    revision_id = Column(PGUUID(as_uuid=True))
    environment_kind = Column(Text, nullable=False)
    environment_id = Column(Text, nullable=False)
    event_name = Column(Text, nullable=False)
    actor_safe_id = Column(Text, nullable=False)
    correlation_id = Column(PGUUID(as_uuid=True), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    version_tags = Column(Text, nullable=False)  # JSONB
    measures = Column(Text, nullable=False)  # JSONB

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "book_id"],
            ["books.tenant_id", "books.book_id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["client_scope.tenant_id", "client_scope.client_id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "workflow_id"],
            ["workflows.tenant_id", "workflows.client_id", "workflows.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        Index("ix_telemetry_measure", "tenant_id", "environment_kind", "event_name", "occurred_at"),
        CheckConstraint("environment_kind IN ('FIXTURE','INSTITUTION_TEST','PRODUCTION')"),
        CheckConstraint("(workflow_id IS NULL AND revision_id IS NULL) OR client_id IS NOT NULL"),
    )
