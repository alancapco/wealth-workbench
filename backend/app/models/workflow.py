"""Workflow orchestration models."""
from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    calendar_event_id = Column(PGUUID(as_uuid=True))
    event_version = Column(Text)
    resolution = Column(Text, nullable=False)
    title = Column(Text)
    starts_at = Column(DateTime(timezone=True))
    ends_at = Column(DateTime(timezone=True))
    row_version = Column(Integer, nullable=False, default=1)
    resolved_by = Column(Text, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["client_scope.tenant_id", "client_scope.client_id"]
        ),
        CheckConstraint("resolution IN ('VERIFIED','RM_CONFIRMED','CONFLICT')"),
        CheckConstraint("row_version > 0"),
        CheckConstraint("ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at"),
    )


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    meeting_id = Column(PGUUID(as_uuid=True))
    workflow_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    current_stage = Column(Text)
    row_version = Column(Integer, nullable=False, default=1)
    context_revision = Column(Integer, nullable=False)
    entry_point = Column(Text, nullable=False)
    task_context = Column(Text)
    created_by = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        UniqueConstraint("tenant_id", "client_id", "id", "meeting_id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["client_scope.tenant_id", "client_scope.client_id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "meeting_id"],
            ["meetings.tenant_id", "meetings.client_id", "meetings.id"]
        ),
        Index("ix_workflow_resume", "tenant_id", "created_by", "status", "updated_at"),
        CheckConstraint("workflow_type IN ('MEETING_PREP','MEETING_FOLLOWUP','OUTREACH','PRODUCT_SEARCH','SHARIAH_REVIEW','HOUSEHOLD_REVIEW')"),
        CheckConstraint("status IN ('NOT_STARTED','RUNNING','NEEDS_REVIEW','PAUSED','BLOCKED','UNAVAILABLE','FAILED','ABANDONED','COMPLETED')"),
        CheckConstraint("row_version > 0"),
        CheckConstraint("context_revision > 0"),
    )


class SkillVersion(Base):
    __tablename__ = "skill_versions"

    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), primary_key=True)
    skill_id = Column(Text, primary_key=True)
    version = Column(Text, primary_key=True)
    handler_key = Column(Text, nullable=False)
    descriptor = Column(Text, nullable=False)  # JSONB
    content_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class StageRun(Base):
    __tablename__ = "stage_runs"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    workflow_id = Column(PGUUID(as_uuid=True), nullable=False)
    stage_key = Column(Text, nullable=False)
    stage_version = Column(Integer, nullable=False)
    status = Column(Text, nullable=False)
    skill_id = Column(Text, nullable=False)
    skill_version = Column(Text, nullable=False)
    context_revision = Column(Integer, nullable=False)
    manual_intervention = Column(Boolean, nullable=False, default=False)
    error_code = Column(Text)
    lease_token = Column(PGUUID(as_uuid=True))
    lease_until = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        UniqueConstraint("tenant_id", "workflow_id", "stage_key", "stage_version"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "workflow_id"],
            ["workflows.tenant_id", "workflows.client_id", "workflows.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "skill_id", "skill_version"],
            ["skill_versions.tenant_id", "skill_versions.skill_id", "skill_versions.version"]
        ),
        Index(
            "ix_stage_claim",
            "status",
            "lease_until",
            postgresql_where="status IN ('PENDING','RUNNING')"
        ),
        CheckConstraint("stage_version > 0"),
        CheckConstraint("status IN ('PENDING','RUNNING','NEEDS_REVIEW','APPROVED','BLOCKED','FAILED','SKIPPED','COMPLETED')"),
    )


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), nullable=False)
    actor_subject = Column(Text, nullable=False)
    provider_key = Column(Text, nullable=False)
    provider_event_id = Column(Text, nullable=False)
    provider_version = Column(Text, nullable=False)
    payload = Column(Text, nullable=False)  # JSONB
    status = Column(Text, nullable=False)
    match_state = Column(Text, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "actor_subject", "provider_key", "provider_event_id", "provider_version"),
        CheckConstraint("status IN ('ACTIVE','CANCELED','INELIGIBLE')"),
        CheckConstraint("match_state IN ('VERIFIED','AMBIGUOUS','UNMATCHED','CONFLICT')"),
    )
