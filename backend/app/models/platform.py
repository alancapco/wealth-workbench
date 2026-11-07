"""Platform and tenant scope models."""
from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class WorkbenchTenant(Base):
    __tablename__ = "workbench_tenants"

    tenant_id = Column(Text, primary_key=True)
    environment_kind = Column(Text, nullable=False)
    environment_id = Column(Text, nullable=False)
    identity_config_ref = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("environment_kind IN ('FIXTURE','INSTITUTION_TEST','PRODUCTION')"),
    )


class Book(Base):
    __tablename__ = "books"

    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), primary_key=True)
    book_id = Column(Text, primary_key=True)
    source_version = Column(Text, nullable=False)
    entitlement_revision = Column(Text, nullable=False)


class ClientScope(Base):
    __tablename__ = "client_scope"

    tenant_id = Column(Text, ForeignKey("workbench_tenants.tenant_id"), primary_key=True)
    client_id = Column(PGUUID(as_uuid=True), ForeignKey("clients.id"), primary_key=True, unique=True)
    context_revision = Column(Integer, nullable=False, default=1)
    ownership_source = Column(Text, nullable=False)
    ownership_version = Column(Text, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("context_revision > 0"),
    )


class ClientAssignment(Base):
    __tablename__ = "client_assignments"

    tenant_id = Column(Text, primary_key=True)
    book_id = Column(Text, primary_key=True)
    client_id = Column(PGUUID(as_uuid=True), primary_key=True)
    entitlement_revision = Column(Text, nullable=False)
    valid = Column(Boolean, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "book_id"],
            ["books.tenant_id", "books.book_id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["client_scope.tenant_id", "client_scope.client_id"]
        ),
    )
