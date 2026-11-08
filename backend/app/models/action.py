"""Action preview, authorization, and outbox models."""
from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ActionPreview(Base):
    __tablename__ = "action_previews"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    revision_id = Column(PGUUID(as_uuid=True), nullable=False)
    action_class = Column(Text, nullable=False)
    preview_hash = Column(String(64), nullable=False)
    request_hash = Column(String(64), nullable=False)
    approved_request = Column(Text, nullable=False)  # JSONB
    provider_key = Column(Text, nullable=False)
    destination_ref = Column(Text, nullable=False)
    environment_kind = Column(Text, nullable=False)
    environment_id = Column(Text, nullable=False)
    context_revision = Column(Integer, nullable=False)
    dependency_manifest = Column(Text, nullable=False)  # JSONB
    status = Column(Text, nullable=False)
    created_by = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        UniqueConstraint("tenant_id", "client_id", "revision_id", "action_class", "provider_key", "destination_ref", "request_hash"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        CheckConstraint("action_class IN ('CRM_WRITE','TASK_WRITE','MEMORY_WRITE','CLIENT_SEND','TICKET_PREFILL')"),
        CheckConstraint("environment_kind IN ('FIXTURE','INSTITUTION_TEST','PRODUCTION')"),
        CheckConstraint("context_revision > 0"),
        CheckConstraint("status IN ('VALID','INVALIDATED','REVOKED')"),
    )


class ActionAuthorization(Base):
    __tablename__ = "action_authorizations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    preview_id = Column(PGUUID(as_uuid=True), nullable=False)
    preview_hash = Column(String(64), nullable=False)
    action_class = Column(Text, nullable=False)
    actor = Column(Text, nullable=False)
    authorized_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Text, nullable=False)
    invalidated_at = Column(DateTime(timezone=True))
    invalidation_code = Column(Text)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        UniqueConstraint("tenant_id", "preview_id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "preview_id"],
            ["action_previews.tenant_id", "action_previews.client_id", "action_previews.id"]
        ),
        CheckConstraint("action_class IN ('CRM_WRITE','TASK_WRITE','MEMORY_WRITE','CLIENT_SEND','TICKET_PREFILL')"),
        CheckConstraint("status IN ('VALID','INVALIDATED','REVOKED')"),
    )


class OutboxAction(Base):
    __tablename__ = "outbox_actions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    authorization_id = Column(PGUUID(as_uuid=True), nullable=False)
    provider_operation_key = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    provider_ref = Column(Text)
    provider_state = Column(Text)
    lease_token = Column(PGUUID(as_uuid=True))
    lease_until = Column(DateTime(timezone=True))
    attempt_count = Column(Integer, nullable=False, default=0)
    submitted_at = Column(DateTime(timezone=True))
    confirmed_at = Column(DateTime(timezone=True))
    readback_at = Column(DateTime(timezone=True))
    last_error_code = Column(Text)
    reconciliation_owner = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        UniqueConstraint("tenant_id", "authorization_id"),
        UniqueConstraint("tenant_id", "provider_operation_key"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "authorization_id"],
            ["action_authorizations.tenant_id", "action_authorizations.client_id", "action_authorizations.id"]
        ),
        Index(
            "ix_outbox_claim",
            "status",
            "lease_until",
            "created_at",
            postgresql_where="status IN ('PENDING','SENDING','UNKNOWN','RECONCILE_REQUIRED')"
        ),
        CheckConstraint("status IN ('PENDING','SENDING','SUCCEEDED','FAILED_SAFE','UNKNOWN','RECONCILE_REQUIRED','CANCELED_BEFORE_DISPATCH')"),
        CheckConstraint("provider_state IN ('ACCEPTED','SCHEDULED','DELIVERED','WRITTEN','PREFILLED','NOT_ACCEPTED','UNKNOWN')"),
        CheckConstraint("attempt_count >= 0"),
    )


class OutboxAttempt(Base):
    __tablename__ = "outbox_attempts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    action_id = Column(PGUUID(as_uuid=True), nullable=False)
    attempt_no = Column(Integer, nullable=False)
    mode = Column(Text, nullable=False)
    lease_token = Column(PGUUID(as_uuid=True), nullable=False)
    status = Column(Text, nullable=False)
    request_hash = Column(String(64), nullable=False)
    receipt_ref = Column(Text)
    error_code = Column(Text)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("tenant_id", "action_id", "attempt_no"),
        UniqueConstraint("tenant_id", "client_id", "action_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "action_id"],
            ["outbox_actions.tenant_id", "outbox_actions.client_id", "outbox_actions.id"]
        ),
        CheckConstraint("attempt_no > 0"),
        CheckConstraint("mode IN ('DISPATCH','READBACK')"),
        CheckConstraint("status IN ('STARTED','CONFIRMED','NOT_ACCEPTED','UNKNOWN')"),
    )


class ClientMemoryEntry(Base):
    __tablename__ = "client_memory_entries"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    memory_key = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    value = Column(Text, nullable=False)  # JSONB
    state = Column(Text, nullable=False)
    source_revision_id = Column(PGUUID(as_uuid=True), nullable=False)
    authorization_id = Column(PGUUID(as_uuid=True), nullable=False)
    confirmed_by = Column(Text, nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        UniqueConstraint("tenant_id", "client_id", "memory_key", "version"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["client_scope.tenant_id", "client_scope.client_id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "source_revision_id"],
            ["artifact_revisions.tenant_id", "artifact_revisions.client_id", "artifact_revisions.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "authorization_id"],
            ["action_authorizations.tenant_id", "action_authorizations.client_id", "action_authorizations.id"]
        ),
        Index("ix_memory_context", "tenant_id", "client_id", "memory_key", "version"),
        CheckConstraint("version > 0"),
        CheckConstraint("state IN ('CONFIRMED','CONFLICT','SUPERSEDED')"),
    )
