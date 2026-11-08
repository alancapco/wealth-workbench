"""AAOIFI knowledge base models for Shariah RAG.

Adapted from islamic-ai/shariah 001_knowledge_graph.sql.
Minimal: standard + clause only (no graph nodes/edges).
"""
from datetime import datetime, UTC

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class AaoifiStandard(Base):
    """AAOIFI standard metadata (e.g. SS 8 Murabahah)."""
    __tablename__ = "aaoifi_standards"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    authority = Column(Text, nullable=False)
    standard_number = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    edition = Column(Text, nullable=False)
    source_checksum = Column(Text, nullable=False)
    approval_status = Column(Text, nullable=False, default="draft")
    language = Column(Text, nullable=False, default="en")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("approval_status IN ('draft','approved','rejected')"),
        UniqueConstraint("authority", "standard_number", "edition", "language", "source_checksum"),
    )


class AaoifiClause(Base):
    """Individual clause within an AAOIFI standard — the searchable unit."""
    __tablename__ = "aaoifi_clauses"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    standard_id = Column(PGUUID(as_uuid=True), ForeignKey("aaoifi_standards.id"), nullable=False)
    clause_id = Column(Text, nullable=False)
    parent_clause_id = Column(Text)
    breadcrumb = Column(Text, nullable=False, default="")
    verbatim_text = Column(Text, nullable=False)
    embedding_text = Column(Text, nullable=False)
    source_pdf_page_start = Column(Integer, nullable=False)
    source_pdf_page_end = Column(Integer, nullable=False)
    printed_page_start = Column(Integer, nullable=False)
    printed_page_end = Column(Integer, nullable=False)
    language = Column(Text, nullable=False, default="en")
    approval_status = Column(Text, nullable=False, default="draft")
    embedding = Column(Vector(1536))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("approval_status IN ('draft','approved','rejected')"),
        UniqueConstraint("standard_id", "clause_id"),
        Index("ix_aaoifi_clauses_standard_approval", "standard_id", "approval_status"),
        Index("ix_aaoifi_clauses_approval", "approval_status"),
        # GIN index for full-text search on embedding_text via tsvector
        Index(
            "ix_aaoifi_clauses_embedding_text_tsv",
            "embedding_text",
            postgresql_using="gin",
            postgresql_ops={"embedding_text": "gin_trgm_ops"},
        ),
    )
