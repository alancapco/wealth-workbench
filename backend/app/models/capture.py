"""Meeting capture, consent, and extraction models."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, BigInteger, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ConsentRecord(Base):
    """Consent for meeting capture - ACCEPTED/DECLINED/WITHDRAWN."""
    __tablename__ = "consent_records"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    meeting_id = Column(PGUUID(as_uuid=True), nullable=False)
    policy_configuration_id = Column(PGUUID(as_uuid=True), nullable=False)
    jurisdiction = Column(Text, nullable=False)
    platform = Column(Text, nullable=False)
    language = Column(Text, nullable=False)
    method = Column(Text, nullable=False)
    participant_refs = Column(JSONB, nullable=False)
    state = Column(Text, nullable=False)
    actor = Column(Text, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    withdrawn_at = Column(DateTime(timezone=True))
    row_version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        UniqueConstraint("tenant_id", "client_id", "meeting_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "meeting_id"],
            ["meetings.tenant_id", "meetings.client_id", "meetings.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "policy_configuration_id"],
            ["configuration_revisions.tenant_id", "configuration_revisions.id"]
        ),
        CheckConstraint("state IN ('ACCEPTED','DECLINED','WITHDRAWN')"),
        CheckConstraint("row_version > 0"),
        CheckConstraint("jsonb_typeof(participant_refs) = 'array'"),
    )


class CaptureSession(Base):
    """Active capture session with lease and segment tracking."""
    __tablename__ = "capture_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    meeting_id = Column(PGUUID(as_uuid=True), nullable=False)
    consent_id = Column(PGUUID(as_uuid=True), nullable=False)
    provider_key = Column(Text, nullable=False)
    provider_ref = Column(Text)
    status = Column(Text, nullable=False)
    row_version = Column(Integer, nullable=False, default=1)
    last_confirmed_audio_ms = Column(BigInteger)
    last_confirmed_transcript_ms = Column(BigInteger)
    lease_valid_until = Column(DateTime(timezone=True))
    lease_revoked = Column(Boolean, nullable=False, default=False)
    error_code = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "client_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "client_id", "meeting_id", "consent_id"],
            ["consent_records.tenant_id", "consent_records.client_id", "consent_records.meeting_id", "consent_records.id"]
        ),
        Index(
            "uq_capture_active_meeting",
            "tenant_id",
            "meeting_id",
            unique=True,
            postgresql_where="status IN ('STARTING','RECORDING','PAUSED','STOPPING')"
        ),
        CheckConstraint("status IN ('STARTING','RECORDING','PAUSED','STOPPING','STOPPED','PROCESSING','PARTIAL','COMPLETE','FAILED')"),
    )
