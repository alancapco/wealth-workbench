"""
Database Models
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Text, nullable=True)  # Additive for multi-tenant architecture
    external_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    aum = Column(Float)
    currency = Column(String, default="USD")
    client_type = Column(String)
    region = Column(String)
    risk_profile = Column(String)
    preferences = Column(JSON, default=dict)
    is_family_office = Column(Boolean, default=False)
    family_entities = Column(JSON, default=list)
    shariah_compliant = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    holdings = relationship("Holding", back_populates="client")
    interactions = relationship("Interaction", back_populates="client")


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"))
    symbol = Column(String, nullable=False)
    quantity = Column(Float)
    cost_basis = Column(Float)
    current_value = Column(Float)
    asset_class = Column(String)
    source_kind = Column(String)
    as_of = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="holdings")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"))
    interaction_date = Column(DateTime, nullable=False)
    interaction_type = Column(String)
    summary = Column(Text)
    preferences_extracted = Column(JSON, default=list)
    action_items = Column(JSON, default=list)
    recording_consent = Column(Boolean, default=False)
    consent_method = Column(String)
    source_kind = Column(String)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="interactions")


class Brief(Base):
    """Brief storage with versioning and artifact linkage.
    
    Legacy columns (id, client_id, version, sections, generated_at, approved_by, 
    approved_at, created_at) remain for backward compatibility.
    
    Additive columns link to artifact lineage when workflow integration is enabled.
    """
    __tablename__ = "briefs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    version = Column(String, nullable=False)
    sections = Column(JSON, nullable=False)
    generated_at = Column(DateTime, nullable=False)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additive artifact linkage columns (all nullable for legacy compatibility)
    tenant_id = Column(Text)
    workflow_id = Column(UUID(as_uuid=True))
    meeting_id = Column(UUID(as_uuid=True))
    artifact_id = Column(UUID(as_uuid=True))
    artifact_revision_id = Column(UUID(as_uuid=True))
    revision_no = Column(Integer)
    source_manifest = Column(JSON)
    content_hash = Column(String(64))
    generated_by = Column(String)


class AuditLog(Base):
    """Audit log for all actions"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
