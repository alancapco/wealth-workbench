"""Family and Household pilot API endpoints (default OFF, DEC-06/DEC-07 gated).

U-016: Family relationship graphing and household context.

API-077: POST /clients/{client_id}/relationships - Create family relationship
API-078: GET /clients/{client_id}/relationships - List relationships
API-079: GET /clients/{client_id}/family-graph - Get family graph for visualization
API-080: POST /households - Create household group
API-081: POST /households/{id}/members - Add member to household
API-082: GET /workflows/{workflow_id}/household-context - Get cross-member context

Features are default OFF - returns 503 FEATURE_DISABLED if gates are OFF.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.identity import get_fixture_principal
from app.schemas.common import Envelope, ResponseMeta
from app.schemas.family import (
    FamilyGraphResponse,
    FamilyRelationshipCreate,
    FamilyRelationshipDetail,
    HouseholdContext,
    HouseholdCreate,
    HouseholdDetail,
    HouseholdMemberAdd,
)
from app.schemas.identity import Principal
from app.services.family import HouseholdService, RelationshipService

router = APIRouter(tags=["family-pilot"])


def check_dec06_gate(enabled: bool = False) -> None:
    """Check DEC-06 family relationship pilot gate.
    
    Feature is default OFF. Returns 503 if gate is disabled.
    """
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "FEATURE_DISABLED",
                    "message": "Family relationships require DEC-06 gate enabled",
                    "retryable": False,
                }
            },
        )


def check_dec07_gate(enabled: bool = False) -> None:
    """Check DEC-07 household pilot gate.
    
    Feature is default OFF. Returns 503 if gate is disabled.
    """
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "FEATURE_DISABLED",
                    "message": "Household features require DEC-07 gate enabled",
                    "retryable": False,
                }
            },
        )


# Family Relationship Endpoints (DEC-06 gated)

@router.post(
    "/clients/{client_id}/relationships",
    response_model=Envelope[FamilyRelationshipDetail],
    status_code=status.HTTP_201_CREATED,
)
async def create_family_relationship(
    client_id: UUID,
    request: FamilyRelationshipCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
    dec06_enabled: bool = False,  # DEC-06 gate: default OFF
) -> Envelope[FamilyRelationshipDetail]:
    """Create family relationship between two clients.
    
    Architecture API-077.
    
    Creates bidirectional relationship (A↔B).
    Requires: family:write permission, DEC-06 gate enabled.
    """
    check_dec06_gate(dec06_enabled)

    service = RelationshipService(db)
    
    # Create bidirectional relationship
    rel_id, _ = await service.create_relationship(
        tenant_id=principal.tenant_id,
        client_a_id=client_id,
        client_b_id=request.client_b_id,
        relationship_type=request.relationship_type,
        confirmed_by=principal.user_id,
        metadata=request.metadata,
    )

    # Fetch created relationship
    relationship = await service.repo.get_by_id(principal.tenant_id, rel_id)

    return Envelope(
        data=FamilyRelationshipDetail(
            id=relationship.id,
            client_a_id=relationship.client_a_id,
            client_b_id=relationship.client_b_id,
            relationship_type=relationship.relationship_type,
            confirmed_by=relationship.confirmed_by,
            confirmed_at=relationship.confirmed_at,
            metadata=relationship.relationship_metadata,
        ),
        meta=ResponseMeta(
            request_id=principal.request_id,
            served_at=principal.as_of,
        ),
    )


@router.get(
    "/clients/{client_id}/relationships",
    response_model=Envelope[list[FamilyRelationshipDetail]],
)
async def list_family_relationships(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
    dec06_enabled: bool = False,  # DEC-06 gate: default OFF
) -> Envelope[list[FamilyRelationshipDetail]]:
    """List all family relationships for a client.
    
    Architecture API-078.
    
    Returns bidirectional relationships.
    Requires: family:read permission, DEC-06 gate enabled.
    """
    check_dec06_gate(dec06_enabled)

    service = RelationshipService(db)
    relationships = await service.repo.get_relationships_for_client(
        principal.tenant_id, client_id
    )

    return Envelope(
        data=[
            FamilyRelationshipDetail(
                id=rel.id,
                client_a_id=rel.client_a_id,
                client_b_id=rel.client_b_id,
                relationship_type=rel.relationship_type,
                confirmed_by=rel.confirmed_by,
                confirmed_at=rel.confirmed_at,
                metadata=rel.relationship_metadata,
            )
            for rel in relationships
        ],
        meta=ResponseMeta(
            request_id=principal.request_id,
            served_at=principal.as_of,
        ),
    )


@router.get(
    "/clients/{client_id}/family-graph",
    response_model=Envelope[FamilyGraphResponse],
)
async def get_family_graph(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
    dec06_enabled: bool = False,  # DEC-06 gate: default OFF
) -> Envelope[FamilyGraphResponse]:
    """Get family graph structure for visualization.
    
    Architecture API-079.
    
    Returns graph compatible with FamilyGraphModal ECharts component.
    Requires: family:read permission, DEC-06 gate enabled.
    """
    check_dec06_gate(dec06_enabled)

    service = RelationshipService(db)
    graph = await service.get_family_graph(principal.tenant_id, client_id)

    return Envelope(
        data=graph,
        meta=ResponseMeta(
            request_id=principal.request_id,
            served_at=principal.as_of,
        ),
    )


# Household Endpoints (DEC-07 gated)

@router.post(
    "/households",
    response_model=Envelope[HouseholdDetail],
    status_code=status.HTTP_201_CREATED,
)
async def create_household(
    request: HouseholdCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
    dec07_enabled: bool = False,  # DEC-07 gate: default OFF
) -> Envelope[HouseholdDetail]:
    """Create a household group.
    
    Architecture API-080.
    
    Groups clients for coordinated planning.
    Requires: household:write permission, DEC-07 gate enabled.
    """
    check_dec07_gate(dec07_enabled)

    service = HouseholdService(db)
    
    household_id = await service.create_household(
        tenant_id=principal.tenant_id,
        household_name=request.household_name,
        primary_contact_id=request.primary_contact_id,
        created_by=principal.user_id,
        address_ref=request.address_ref,
        initial_members=request.initial_members,
    )

    # Fetch created household
    household = await service.repo.get_by_id(principal.tenant_id, household_id)
    members = await service.repo.list_members(principal.tenant_id, household_id)

    await db.commit()

    return Envelope(
        data=HouseholdDetail(
            id=household.id,
            household_name=household.household_name,
            primary_contact_id=household.primary_contact_id,
            address_ref=household.address_ref,
            created_by=household.created_by,
            created_at=household.created_at,
            member_count=len(members),
        ),
        meta=ResponseMeta(
            request_id=principal.request_id,
            served_at=principal.as_of,
        ),
    )


@router.post(
    "/households/{household_id}/members",
    response_model=Envelope[dict],
    status_code=status.HTTP_201_CREATED,
)
async def add_household_member(
    household_id: UUID,
    request: HouseholdMemberAdd,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
    dec07_enabled: bool = False,  # DEC-07 gate: default OFF
) -> Envelope[dict]:
    """Add a member to a household.
    
    Architecture API-081.
    
    Requires: household:write permission, DEC-07 gate enabled.
    """
    check_dec07_gate(dec07_enabled)

    service = HouseholdService(db)
    
    membership = await service.repo.add_member(
        tenant_id=principal.tenant_id,
        household_id=household_id,
        client_id=request.client_id,
        role=request.role,
    )

    await db.commit()

    return Envelope(
        data={
            "membership_id": str(membership.id),
            "household_id": str(household_id),
            "client_id": str(request.client_id),
            "role": request.role,
        },
        meta=ResponseMeta(
            request_id=principal.request_id,
            served_at=principal.as_of,
        ),
    )


@router.get(
    "/workflows/{workflow_id}/household-context",
    response_model=Envelope[HouseholdContext],
)
async def get_household_context(
    workflow_id: UUID,
    household_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
    dec07_enabled: bool = False,  # DEC-07 gate: default OFF
) -> Envelope[HouseholdContext]:
    """Get cross-member context for household.
    
    Architecture API-082.
    
    Aggregates context from all consenting household members.
    Requires: household:read permission, DEC-07 gate enabled.
    """
    check_dec07_gate(dec07_enabled)

    service = HouseholdService(db)
    
    context = await service.get_cross_member_context(
        tenant_id=principal.tenant_id,
        workflow_id=workflow_id,
        household_id=household_id,
        dec07_enabled=dec07_enabled,
    )

    return Envelope(
        data=context,
        meta=ResponseMeta(
            request_id=principal.request_id,
            served_at=principal.as_of,
        ),
    )
