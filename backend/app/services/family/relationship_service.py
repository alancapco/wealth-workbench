"""Relationship service for family graph management (U-016, DEC-06 gated)."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.family import RelationshipRepository
from app.schemas.family import FamilyGraphEdge, FamilyGraphNode, FamilyGraphResponse


class RelationshipService:
    """Service for managing family relationships and graphs."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RelationshipRepository(session)

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
        
        Returns both relationship IDs (A→B and B→A).
        """
        # Create A → B relationship
        rel_ab = await self.repo.create(
            tenant_id=tenant_id,
            client_a_id=client_a_id,
            client_b_id=client_b_id,
            relationship_type=relationship_type,
            confirmed_by=confirmed_by,
            metadata=metadata,
        )

        # Create inverse relationship type for B → A
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
        """Generate family graph structure for visualization.
        
        Returns graph with nodes and edges compatible with ECharts.
        """
        # Get all relationships for this client
        relationships = await self.repo.get_relationships_for_client(tenant_id, client_id)

        # Build nodes set (unique clients)
        node_ids = {client_id}
        for rel in relationships:
            node_ids.add(rel.client_a_id)
            node_ids.add(rel.client_b_id)

        # Create nodes (simplified - in production would fetch client names)
        nodes = [
            FamilyGraphNode(
                id=str(node_id),
                name=f"Client {str(node_id)[:8]}",
                symbolSize=80 if node_id == client_id else 60,
                category=0,
            )
            for node_id in node_ids
        ]

        # Create edges
        edges = [
            FamilyGraphEdge(
                source=str(rel.client_a_id),
                target=str(rel.client_b_id),
                relationship_type=rel.relationship_type,
            )
            for rel in relationships
        ]

        return FamilyGraphResponse(
            nodes=nodes,
            links=edges,
            categories=[{"name": "Family Member"}],
        )

    def validate_relationship_consent(
        self, client_a_consented: bool, client_b_consented: bool
    ) -> bool:
        """Validate that both parties have consented to the relationship."""
        return client_a_consented and client_b_consented

    def _get_inverse_relationship(self, relationship_type: str) -> str:
        """Get inverse relationship type for bidirectional relationships."""
        inverses = {
            "SPOUSE": "SPOUSE",  # Symmetric
            "PARENT": "CHILD",
            "CHILD": "PARENT",
            "SIBLING": "SIBLING",  # Symmetric
            "OTHER": "OTHER",  # Symmetric
        }
        return inverses.get(relationship_type, "OTHER")
