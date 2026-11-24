"""Family and Household pilot API endpoints (DEC-06/DEC-07 configurable gates).

U-016: Family relationship graphing and household context.

API-077: POST /clients/{client_id}/relationships - Create family relationship
API-078: GET /clients/{client_id}/relationships - List relationships
API-079: GET /clients/{client_id}/family-graph - Get family graph for visualization
API-080: POST /households - Create household group
API-081: POST /households/{id}/members - Add member to household
API-082: GET /workflows/{workflow_id}/household-context - Get cross-member context

Gates are driven by Settings (FAMILY_DEC06_ENABLED / HOUSEHOLD_DEC07_ENABLED).
They used to be hardcoded `False` function arguments, which made every request
return 503 FEATURE_DISABLED and exposed the gate as a bypassable query parameter.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.identity import get_fixture_principal
from app.models.models import Client
from app.schemas.common import Envelope, ResponseMeta
from app.schemas.family import (
    FamilyGraphEdge,
    FamilyGraphNode,
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


def _meta() -> ResponseMeta:
    """Build response metadata from real values.

    `Principal` has no `request_id` or `as_of` attributes (see
    app/schemas/identity.py), so reading them here previously raised
    AttributeError -> HTTP 500 as soon as the gate was opened.
    """
    return ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))


def _error(status_code: int, code: str, message: str) -> HTTPException:
    """Consistent canonical error envelope (`detail.error.*`)."""
    return HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message, "retryable": False}},
    )


async def _require_clients(db: AsyncSession, tenant_id: str, *client_ids: UUID) -> None:
    """Validate composite-FK endpoints before writing.

    family_relationships, household_groups and household_memberships all carry
    FKs on (tenant_id, client_id) -> clients(tenant_id, id). Without this check
    a stale or cross-tenant id surfaced as an unhandled IntegrityError -> 500.
    """
    wanted = list(dict.fromkeys(client_ids))
    stmt = select(Client.id).where(Client.id.in_(wanted), Client.tenant_id == tenant_id)
    found = set((await db.execute(stmt)).scalars().all())
    missing = [str(c) for c in wanted if c not in found]
    if missing:
        raise _error(
            404,
            "CLIENT_NOT_FOUND",
            f"Clients not found in this tenant: {', '.join(missing)}",
        )


def check_dec06_gate(enabled: bool = False) -> None:
    """Check DEC-06 family relationship pilot gate (settings-driven)."""
    if not enabled:
        raise _error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "FEATURE_DISABLED",
            "Family relationships require DEC-06 gate enabled (FAMILY_DEC06_ENABLED)",
        )


def check_dec07_gate(enabled: bool = False) -> None:
    """Check DEC-07 household pilot gate (settings-driven)."""
    if not enabled:
        raise _error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "FEATURE_DISABLED",
            "Household features require DEC-07 gate enabled (HOUSEHOLD_DEC07_ENABLED)",
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
) -> Envelope[FamilyRelationshipDetail]:
    """Create a bidirectional family relationship (A<->B). Architecture API-077."""
    check_dec06_gate(settings.FAMILY_DEC06_ENABLED)
    await _require_clients(db, principal.tenant_id, client_id, request.client_b_id)

    service = RelationshipService(db)
    try:
        rel_id, _ = await service.create_relationship(
            tenant_id=principal.tenant_id,
            client_a_id=client_id,
            client_b_id=request.client_b_id,
            relationship_type=request.relationship_type,
            confirmed_by=principal.subject,
            metadata=request.metadata,
        )
        # get_db() deliberately does not commit (see app/core/database.py);
        # without this the endpoint returned 201 for rows that were rolled back.
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise _error(
            409,
            "RELATIONSHIP_CONFLICT",
            "Relationship already exists, or a client is outside this tenant.",
        ) from exc

    relationship = await service.repo.get_by_id(principal.tenant_id, rel_id)
    if relationship is None:
        raise _error(404, "RELATIONSHIP_NOT_FOUND", "Created relationship could not be reloaded.")

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
        meta=_meta(),
    )


@router.get(
    "/clients/{client_id}/relationships",
    response_model=Envelope[list[FamilyRelationshipDetail]],
)
async def list_family_relationships(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
) -> Envelope[list[FamilyRelationshipDetail]]:
    """List all family relationships for a client. Architecture API-078."""
    check_dec06_gate(settings.FAMILY_DEC06_ENABLED)

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
        meta=_meta(),
    )


@router.get(
    "/clients/{client_id}/family-graph",
    response_model=Envelope[FamilyGraphResponse],
)
async def get_family_graph(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
) -> Envelope[FamilyGraphResponse]:
    """Get family graph structure for visualisation. Architecture API-079."""
    check_dec06_gate(settings.FAMILY_DEC06_ENABLED)

    service = RelationshipService(db)
    graph = await service.get_family_graph(principal.tenant_id, client_id)
    if not graph.links:
        from app.services.graph.neo4j_service import client_graph

        wealth = await client_graph(db, client_id)
        if wealth and wealth.get("nodes"):
            graph = FamilyGraphResponse(
                nodes=[
                    FamilyGraphNode(
                        id=node["id"],
                        name=node["name"],
                        symbolSize=int(node.get("symbolSize") or 28),
                        category=int(node.get("category") or 0),
                        label={"show": True},
                        entitlement=node.get("entitlement"),
                        kind=node.get("kind"),
                        is_root=bool(node.get("is_root")),
                    )
                    for node in wealth["nodes"]
                ],
                links=[
                    FamilyGraphEdge(
                        source=link["source"],
                        target=link["target"],
                        relationship_type=link["relationship_type"],
                        value=float(link.get("value") or 1),
                    )
                    for link in wealth["links"]
                ],
                categories=wealth.get("categories") or [{"name": "Client"}],
                root_id=wealth.get("root_id"),
            )

    return Envelope(data=graph, meta=_meta())


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
) -> Envelope[HouseholdDetail]:
    """Create a household group. Architecture API-080."""
    check_dec07_gate(settings.HOUSEHOLD_DEC07_ENABLED)
    await _require_clients(
        db, principal.tenant_id, request.primary_contact_id, *request.initial_members
    )

    service = HouseholdService(db)
    try:
        household_id = await service.create_household(
            tenant_id=principal.tenant_id,
            household_name=request.household_name,
            primary_contact_id=request.primary_contact_id,
            created_by=principal.subject,
            address_ref=request.address_ref,
            initial_members=request.initial_members,
        )
        household = await service.repo.get_by_id(principal.tenant_id, household_id)
        members = await service.repo.list_members(principal.tenant_id, household_id)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise _error(
            409, "HOUSEHOLD_CONFLICT", "Household could not be created for these clients."
        ) from exc

    if household is None:
        raise _error(404, "HOUSEHOLD_NOT_FOUND", "Created household could not be reloaded.")

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
        meta=_meta(),
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
) -> Envelope[dict]:
    """Add a member to a household. Architecture API-081."""
    check_dec07_gate(settings.HOUSEHOLD_DEC07_ENABLED)
    await _require_clients(db, principal.tenant_id, request.client_id)

    service = HouseholdService(db)
    try:
        membership = await service.repo.add_member(
            tenant_id=principal.tenant_id,
            household_id=household_id,
            client_id=request.client_id,
            role=request.role,
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise _error(
            409,
            "HOUSEHOLD_MEMBER_CONFLICT",
            "Member already exists, or household/client is outside this tenant.",
        ) from exc

    return Envelope(
        data={
            "membership_id": str(membership.id),
            "household_id": str(household_id),
            "client_id": str(request.client_id),
            "role": request.role,
        },
        meta=_meta(),
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
) -> Envelope[HouseholdContext]:
    """Get cross-member context for household. Architecture API-082."""
    check_dec07_gate(settings.HOUSEHOLD_DEC07_ENABLED)

    service = HouseholdService(db)
    context = await service.get_cross_member_context(
        tenant_id=principal.tenant_id,
        workflow_id=workflow_id,
        household_id=household_id,
        dec07_enabled=settings.HOUSEHOLD_DEC07_ENABLED,
    )

    return Envelope(data=context, meta=_meta())
