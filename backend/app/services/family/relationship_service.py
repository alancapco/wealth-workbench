"""Relationship service for family graph management (U-016, DEC-06 gated).

The graph is assembled only from persisted data:

* the ``Client`` row (``name``, ``family_entities``),
* the declared ``parent`` links inside ``family_entities``,
* real rows in ``family_relationships``.

No AUM, ownership percentage or valuation is invented here. ``symbolSize`` is a
relative *visual* weight derived from entity kind, never a monetary amount.
"""
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Client
from app.repositories.family import RelationshipRepository
from app.schemas.family import FamilyGraphEdge, FamilyGraphNode, FamilyGraphResponse

CATEGORIES = [
    {"name": "Family office"},
    {"name": "Trust"},
    {"name": "Family member"},
    {"name": "Operating entity"},
    {"name": "Related client"},
]

KIND_CATEGORY = {"TRUST": 1, "PERSON": 2, "COMPANY": 3, "FOUNDATION": 3}
KIND_SIZE = {"TRUST": 28, "PERSON": 24, "COMPANY": 26, "FOUNDATION": 26}
RELATED_CLIENT_CATEGORY = 4


class RelationshipService:
    """Service for managing family relationships and graphs."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RelationshipRepository(session)

    async def _client(self, client_id: UUID, tenant_id: str) -> Client | None:
        """Load a client, tolerating legacy seeded rows with a NULL tenant_id."""
        stmt = select(Client).where(
            Client.id == client_id,
            or_(Client.tenant_id == tenant_id, Client.tenant_id.is_(None)),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_relationship(
        self,
        tenant_id: str,
        client_a_id: UUID,
        client_b_id: UUID,
        relationship_type: str,
        confirmed_by: str,
        metadata: dict | None = None,
    ) -> tuple[UUID, UUID]:
        """Create bidirectional family relationship.

        Returns both relationship IDs (A->B and B->A).
        """
        rel_ab = await self.repo.create(
            tenant_id=tenant_id,
            client_a_id=client_a_id,
            client_b_id=client_b_id,
            relationship_type=relationship_type,
            confirmed_by=confirmed_by,
            metadata=metadata,
        )

        inverse_type = self._get_inverse_relationship(relationship_type)
        rel_ba = await self.repo.create(
            tenant_id=tenant_id,
            client_a_id=client_b_id,
            client_b_id=client_a_id,
            relationship_type=inverse_type,
            confirmed_by=confirmed_by,
            metadata=metadata,
        )

        return rel_ab.id, rel_ba.id

    async def get_family_graph(
        self, tenant_id: str, client_id: UUID
    ) -> FamilyGraphResponse:
        """Build a graph from real client, household-entity and relationship rows.

        ``family_entities`` entries are dictionaries of the form
        ``{name, entitlement, kind, parent}``. ``parent`` is a *declared* link to
        another entity name; when absent the entity hangs off the household root.
        Nothing is inferred from display names and no numbers are fabricated.
        """
        root = await self._client(client_id, tenant_id)
        root_id = str(root.id) if root else str(client_id)
        root_name = root.name if root else f"Client {str(client_id)[:8]}"

        nodes: list[FamilyGraphNode] = [
            FamilyGraphNode(
                id=root_id,
                name=root_name,
                symbolSize=34,
                category=0,
                kind="FAMILY_OFFICE",
                is_root=True,
            )
        ]
        links: list[FamilyGraphEdge] = []
        known_ids: set[str] = {root_id}

        raw_entities = (root.family_entities if root and root.family_entities else []) or []
        entities = [e for e in raw_entities if isinstance(e, dict)]
        declared: list[tuple[str, str | None]] = []
        entity_ids: dict[str, str] = {}

        for entity in entities:
            name = str(entity.get("name") or "").strip()
            if not name:
                continue
            eid = str(uuid5(NAMESPACE_URL, f"{root_id}:{name}"))
            entity_ids[name] = eid
            kind = str(entity.get("kind") or "TRUST").upper()
            declared.append((name, str(entity["parent"]).strip() if entity.get("parent") else None))
            nodes.append(
                FamilyGraphNode(
                    id=eid,
                    name=name,
                    symbolSize=KIND_SIZE.get(kind, 24),
                    category=KIND_CATEGORY.get(kind, 1),
                    entitlement=entity.get("entitlement"),
                    kind=kind,
                )
            )
            known_ids.add(eid)

        for name, parent in declared:
            child_id = entity_ids.get(name)
            if not child_id:
                continue
            parent_id = entity_ids.get(parent) if parent else None
            if parent_id and parent_id != child_id:
                links.append(
                    FamilyGraphEdge(
                        source=parent_id,
                        target=child_id,
                        relationship_type="OWNERSHIP",
                    )
                )
            else:
                links.append(
                    FamilyGraphEdge(
                        source=root_id,
                        target=child_id,
                        relationship_type="HOUSEHOLD_ENTITY",
                    )
                )

        # Overlay persisted client-to-client relationships. The repository stores
        # each link twice (A->B and B->A), so dedupe on the unordered pair.
        relationships = await self.repo.get_relationships_for_client(tenant_id, client_id)
        seen_pairs: set[frozenset[str]] = set()
        for rel in relationships:
            a, b = str(rel.client_a_id), str(rel.client_b_id)
            if a == b:
                continue
            pair = frozenset((a, b))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            for cid in (a, b):
                if cid in known_ids:
                    continue
                try:
                    other = await self._client(UUID(cid), tenant_id)
                except (ValueError, TypeError):
                    other = None
                nodes.append(
                    FamilyGraphNode(
                        id=cid,
                        name=other.name if other else f"Client {cid[:8]}",
                        symbolSize=24,
                        category=RELATED_CLIENT_CATEGORY,
                        kind="CLIENT",
                    )
                )
                known_ids.add(cid)

            links.append(
                FamilyGraphEdge(
                    source=a,
                    target=b,
                    relationship_type=rel.relationship_type,
                )
            )

        return FamilyGraphResponse(
            nodes=nodes,
            links=links,
            categories=[dict(c) for c in CATEGORIES],
            root_id=root_id,
        )

    def validate_relationship_consent(
        self, client_a_consented: bool, client_b_consented: bool
    ) -> bool:
        """Validate that both parties have consented to the relationship."""
        return client_a_consented and client_b_consented

    def _get_inverse_relationship(self, relationship_type: str) -> str:
        """Get inverse relationship type for bidirectional relationships."""
        inverses = {
            "SPOUSE": "SPOUSE",
            "PARENT": "CHILD",
            "CHILD": "PARENT",
            "SIBLING": "SIBLING",
            "OTHER": "OTHER",
        }
        return inverses.get(relationship_type, "OTHER")
