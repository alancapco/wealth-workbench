"""Client memory models.

``ClientMemoryRecord`` is the pilot memory workflow (API-013 / API-014) with an
explicit review state. ``ClientMemory`` is the lightweight relationship-context
table used by MemoryService; it lives here so it is registered with
Base.metadata, discoverable by Alembic, and importable from app.models.
"""
from datetime import datetime
import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import TIMESTAMP

from app.core.database import Base


class ClientMemoryRecord(Base):
    __tablename__ = "client_memory_records"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    entry_type = Column(Text, nullable=False)  # PREFERENCE | FACT | CONSTRAINT | GOAL
    content = Column(Text, nullable=False)
    source_ref = Column(Text, nullable=False)
    state = Column(Text, nullable=False)  # NEEDS_REVIEW | CONFIRMED | REJECTED
    confidence = Column(Text, nullable=True)
    proposed_by = Column(Text, nullable=True)
    proposed_at = Column(TIMESTAMP(timezone=True), nullable=False)
    reviewed_by = Column(Text, nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('PREFERENCE', 'FACT', 'CONSTRAINT', 'GOAL')",
            name="ck_memory_record_type",
        ),
        CheckConstraint(
            "state IN ('NEEDS_REVIEW', 'CONFIRMED', 'REJECTED')",
            name="ck_memory_record_state",
        ),
        Index(
            "ix_memory_record_client_state",
            "tenant_id", "client_id", "state", "created_at",
        ),
    )


class ClientMemory(Base):
    """Persistent client memory and relationship graph (lightweight store)."""
    __tablename__ = "client_memories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(PGUUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    memory_type = Column(String, nullable=False)  # preference, relationship, context
    key = Column(String, nullable=False)
    value = Column(Text)
    # "metadata" is reserved by SQLAlchemy's declarative base.
    extra_metadata = Column(JSON, default=dict)
    confidence = Column(String)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
