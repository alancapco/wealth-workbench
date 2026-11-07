"""Family and Household pilot models - default OFF, DEC-06/DEC-07 gated.

U-016: Family relationship graphing and household grouping (pilot).
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from app.core.database import Base


class FamilyRelationship(Base):
    """Family relationships between clients (bidirectional).
    
    Architecture §6.11: Relationship graphing for coordinated wealth planning.
    DEC-06 gated (default OFF).
    """
    __tablename__ = "family_relationships"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    client_a_id = Column(PGUUID(as_uuid=True), nullable=False)
    client_b_id = Column(PGUUID(as_uuid=True), nullable=False)
    relationship_type = Column(Text, nullable=False)
    confirmed_by = Column(Text, nullable=False)  # user_id who confirmed
    confirmed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    relationship_metadata = Column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "client_a_id", "client_b_id", "relationship_type"),
        CheckConstraint(
            "relationship_type IN ('SPOUSE','PARENT','CHILD','SIBLING','OTHER')"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_a_id"],
            ["clients.tenant_id", "clients.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_b_id"],
            ["clients.tenant_id", "clients.id"],
        ),
    )


class HouseholdGroup(Base):
    """Household grouping for coordinated planning.
    
    Architecture §6.11: Cross-member context with consent.
    DEC-07 gated (default OFF).
    """
    __tablename__ = "household_groups"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    household_name = Column(Text, nullable=False)
    primary_contact_id = Column(PGUUID(as_uuid=True), nullable=False)
    address_ref = Column(Text)  # Optional reference to shared address
    created_by = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "primary_contact_id"],
            ["clients.tenant_id", "clients.id"],
        ),
    )


class HouseholdMembership(Base):
    """Membership in a household group.
    
    Architecture §6.11: Members can consent to share context.
    """
    __tablename__ = "household_memberships"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(Text, nullable=False)
    household_id = Column(PGUUID(as_uuid=True), nullable=False)
    client_id = Column(PGUUID(as_uuid=True), nullable=False)
    role = Column(Text, nullable=False)  # PRIMARY or MEMBER
    joined_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "household_id", "client_id"),
        CheckConstraint("role IN ('PRIMARY','MEMBER')"),
        ForeignKeyConstraint(
            ["tenant_id", "household_id"],
            ["household_groups.tenant_id", "household_groups.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["clients.tenant_id", "clients.id"],
        ),
    )
