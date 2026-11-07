"""Priority evaluation, controls and contact outcomes persistence.

Architecture §6.6, SQL priority_evaluations/priority_items/priority_controls/contact_outcomes tables.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PriorityEvaluation(Base):
    """Book-wide priority evaluation per architecture §6.6 API-015/016."""
    
    __tablename__ = "priority_evaluations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    book_id = Column(Text, nullable=False)
    local_date = Column(Date, nullable=False)
    timezone = Column(Text, nullable=False)
    policy_configuration_id = Column(PGUUID(as_uuid=True), nullable=False)
    status = Column(Text, nullable=False)  # CURRENT|STALE|FAILED
    criteria_summary = Column(Text, nullable=False)
    evaluated_at = Column(TIMESTAMP(timezone=True), nullable=False)
    environment_kind = Column(Text, nullable=False)  # FIXTURE|INSTITUTION_TEST|PRODUCTION
    environment_id = Column(Text, nullable=False)
    created_by = Column(Text, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "book_id", "id", name="uq_priority_eval_tenant_book_id"),
        ForeignKeyConstraint(
            ["tenant_id", "book_id"],
            ["books.tenant_id", "books.book_id"],
            name="fk_priority_eval_book"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "policy_configuration_id"],
            ["configuration_revisions.tenant_id", "configuration_revisions.id"],
            name="fk_priority_eval_policy"
        ),
        CheckConstraint(
            "status IN ('CURRENT', 'STALE', 'FAILED')",
            name="ck_priority_eval_status"
        ),
        CheckConstraint(
            "environment_kind IN ('FIXTURE', 'INSTITUTION_TEST', 'PRODUCTION')",
            name="ck_priority_eval_env_kind"
        ),
        Index(
            "ix_priority_latest",
            "tenant_id", "book_id", "local_date",
            postgresql_ops={"evaluated_at": "DESC"}
        ),
    )
    
    # Relationships
    items = relationship("PriorityItem", back_populates="evaluation", cascade="all, delete-orphan")


class PriorityItem(Base):
    """Priority ranked client with reasons per architecture §6.6."""
    
    __tablename__ = "priority_items"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    book_id = Column(Text, nullable=False)
    evaluation_id = Column(PGUUID(as_uuid=True), nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    rank = Column(Integer, nullable=False)
    reasons = Column(JSONB, nullable=False)  # Array of PriorityReason JSON
    rank_change_explanation = Column(Text, nullable=True)
    last_updated_at = Column(TIMESTAMP(timezone=True), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "evaluation_id", "client_id", name="uq_priority_item_eval_client"),
        UniqueConstraint("tenant_id", "evaluation_id", "rank", name="uq_priority_item_eval_rank"),
        UniqueConstraint("tenant_id", "book_id", "evaluation_id", "client_id", name="uq_priority_item_book_eval_client"),
        ForeignKeyConstraint(
            ["tenant_id", "book_id", "evaluation_id"],
            ["priority_evaluations.tenant_id", "priority_evaluations.book_id", "priority_evaluations.id"],
            name="fk_priority_item_evaluation"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "book_id", "client_id"],
            ["client_assignments.tenant_id", "client_assignments.book_id", "client_assignments.client_id"],
            name="fk_priority_item_client_assignment"
        ),
        CheckConstraint("rank BETWEEN 1 AND 10", name="ck_priority_item_rank"),
    )
    
    # Relationships
    evaluation = relationship("PriorityEvaluation", back_populates="items")
    controls = relationship("PriorityControl", back_populates="item", cascade="all, delete-orphan")
    outcomes = relationship("ContactOutcome", back_populates="item", cascade="all, delete-orphan")


class PriorityControl(Base):
    """RM controls (snooze/dismiss/pin) per architecture §6.6 API-054."""
    
    __tablename__ = "priority_controls"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    book_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    evaluation_id = Column(PGUUID(as_uuid=True), nullable=False)
    reason_key = Column(Text, nullable=False)
    reason_hash = Column(String(64), nullable=False)
    control_type = Column(Text, nullable=False)  # SNOOZE|DISMISS|PIN
    until_at = Column(TIMESTAMP(timezone=True), nullable=True)
    pinned = Column(Integer, nullable=True)  # boolean as integer
    reason = Column(JSONB, nullable=True)  # Reason JSON
    policy_configuration_id = Column(PGUUID(as_uuid=True), nullable=False)
    actor = Column(Text, nullable=False)
    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False)
    row_version = Column(Integer, nullable=False)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "book_id", "evaluation_id", "client_id"],
            ["priority_items.tenant_id", "priority_items.book_id", "priority_items.evaluation_id", "priority_items.client_id"],
            name="fk_priority_control_item"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "policy_configuration_id"],
            ["configuration_revisions.tenant_id", "configuration_revisions.id"],
            name="fk_priority_control_policy"
        ),
        CheckConstraint(
            "control_type IN ('SNOOZE', 'DISMISS', 'PIN')",
            name="ck_priority_control_type"
        ),
        CheckConstraint(
            "(control_type='SNOOZE' AND until_at IS NOT NULL AND until_at > recorded_at) OR "
            "(control_type='DISMISS' AND reason IS NOT NULL) OR "
            "(control_type='PIN' AND pinned IS NOT NULL)",
            name="ck_priority_control_fields"
        ),
        CheckConstraint("row_version > 0", name="ck_priority_control_row_version"),
    )
    
    # Relationships
    item = relationship("PriorityItem", back_populates="controls")


class ContactOutcome(Base):
    """Contact outcome recording per architecture §6.6 API-055."""
    
    __tablename__ = "contact_outcomes"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    book_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    evaluation_id = Column(PGUUID(as_uuid=True), nullable=False)
    reason_key = Column(Text, nullable=False)
    reason_hash = Column(String(64), nullable=False)
    outcome = Column(Text, nullable=False)  # CONTACTED|MEETING_BOOKED|NO_RESPONSE|NOT_RELEVANT
    occurred_at = Column(TIMESTAMP(timezone=True), nullable=False)
    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False)
    note = Column(Text, nullable=True)
    meeting_id = Column(PGUUID(as_uuid=True), nullable=True)
    evidence_refs = Column(JSONB, nullable=False, server_default="[]")
    meaningful_touchpoint = Column(Text, nullable=False)  # CONFIRMED|NOT_CONFIRMED|UNCONFIGURED
    actor = Column(Text, nullable=False)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "book_id", "evaluation_id", "client_id"],
            ["priority_items.tenant_id", "priority_items.book_id", "priority_items.evaluation_id", "priority_items.client_id"],
            name="fk_contact_outcome_item"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "meeting_id"],
            ["meetings.tenant_id", "meetings.client_id", "meetings.id"],
            name="fk_contact_outcome_meeting"
        ),
        CheckConstraint(
            "outcome IN ('CONTACTED', 'MEETING_BOOKED', 'NO_RESPONSE', 'NOT_RELEVANT')",
            name="ck_contact_outcome_outcome"
        ),
        CheckConstraint(
            "meaningful_touchpoint IN ('CONFIRMED', 'NOT_CONFIRMED', 'UNCONFIGURED')",
            name="ck_contact_outcome_touchpoint"
        ),
        CheckConstraint("occurred_at <= recorded_at", name="ck_contact_outcome_time_order"),
    )
    
    # Relationships
    item = relationship("PriorityItem", back_populates="outcomes")
