"""Family and Household pilot schemas - U-016.

DEC-06 gated (family relationships), DEC-07 gated (households).
"""
from datetime import datetime, UTC
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Family Relationship Schemas
class FamilyRelationshipCreate(BaseModel):
    """Request to create a family relationship."""
    model_config = ConfigDict(extra="forbid")

    client_b_id: UUID = Field(..., description="Other client in the relationship")
    relationship_type: Literal["SPOUSE", "PARENT", "CHILD", "SIBLING", "OTHER"]
    metadata: dict = Field(default_factory=dict)


class FamilyRelationshipDetail(BaseModel):
    """Family relationship detail response."""
    model_config = ConfigDict(extra="forbid")

    id: UUID
    client_a_id: UUID
    client_b_id: UUID
    relationship_type: Literal["SPOUSE", "PARENT", "CHILD", "SIBLING", "OTHER"]
    confirmed_by: str
    confirmed_at: datetime
    metadata: dict


# Household Schemas
class HouseholdCreate(BaseModel):
    """Request to create a household group."""
    model_config = ConfigDict(extra="forbid")

    household_name: str = Field(..., min_length=1, max_length=200)
    primary_contact_id: UUID
    address_ref: str | None = None
    initial_members: list[UUID] = Field(default_factory=list, description="Additional members to add")


class HouseholdMemberAdd(BaseModel):
    """Request to add a member to a household."""
    model_config = ConfigDict(extra="forbid")

    client_id: UUID
    role: Literal["PRIMARY", "MEMBER"] = "MEMBER"


class HouseholdDetail(BaseModel):
    """Household group detail response."""
    model_config = ConfigDict(extra="forbid")

    id: UUID
    household_name: str
    primary_contact_id: UUID
    address_ref: str | None
    created_by: str
    created_at: datetime
    member_count: int


# Family Graph Visualization Schemas
class FamilyGraphNode(BaseModel):
    """Node in the family graph, consumed by ECharts and d3-force alike."""
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    symbolSize: int = Field(default=60)
    category: int = Field(default=0, description="Index into FamilyGraphResponse.categories")
    label: dict = Field(default_factory=lambda: {"show": True})
    entitlement: str | None = Field(
        default=None, description="Declared data entitlement for a household entity"
    )
    kind: str | None = Field(
        default=None,
        description="FAMILY_OFFICE | TRUST | PERSON | COMPANY | CLIENT",
    )
    is_root: bool = Field(default=False)


class FamilyGraphEdge(BaseModel):
    """Edge in the family graph."""
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    relationship_type: str
    value: float = Field(default=1.0)


class FamilyGraphResponse(BaseModel):
    """Graph structure (nodes / links / categories) for ECharts or d3-force."""
    model_config = ConfigDict(extra="forbid")

    nodes: list[FamilyGraphNode]
    links: list[FamilyGraphEdge]
    categories: list[dict] = Field(
        default_factory=lambda: [{"name": "Family Member"}]
    )
    root_id: str | None = Field(
        default=None, description="Household root node id, used to anchor the layout"
    )


# Household Context Schema
class HouseholdContext(BaseModel):
    """Aggregated cross-member context for household."""
    model_config = ConfigDict(extra="forbid")

    household_id: UUID
    household_name: str
    member_contexts: list[dict] = Field(
        default_factory=list,
        description="Context from consenting members"
    )
    total_members: int
    consenting_members: int
    aggregated_at: datetime
