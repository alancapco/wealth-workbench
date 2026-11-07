"""Family and Household pilot schemas - U-016.

DEC-06 gated (family relationships), DEC-07 gated (households).
"""
from datetime import datetime
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
    """Node in family graph for visualization."""
    model_config = ConfigDict(extra="forbid")

    id: str  # client_id as string
    name: str
    symbolSize: int = Field(default=60)
    category: int = Field(default=0, description="Node category for coloring")
    label: dict = Field(default_factory=lambda: {"show": True})


class FamilyGraphEdge(BaseModel):
    """Edge in family graph for visualization."""
    model_config = ConfigDict(extra="forbid")

    source: str  # client_id as string
    target: str  # client_id as string
    relationship_type: str
    value: float = Field(default=1.0)


class FamilyGraphResponse(BaseModel):
    """Family graph structure for ECharts visualization."""
    model_config = ConfigDict(extra="forbid")

    nodes: list[FamilyGraphNode]
    links: list[FamilyGraphEdge]
    categories: list[dict] = Field(
        default_factory=lambda: [{"name": "Family Member"}]
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
