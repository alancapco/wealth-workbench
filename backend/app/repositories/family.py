"""Repository layer for family and household pilot (U-016)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family import FamilyRelationship, HouseholdGroup, HouseholdMembership
from app.repositories.base import TenantScopedRepository


class RelationshipRepository(TenantScopedRepository[FamilyRelationship]):
    """Repository for family relationships with tenant isolation."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, FamilyRelationship)

    async def create(
        self,
        tenant_id: str,
        client_a_id: UUID,
        client_b_id: UUID,
        relationship_type: str,
        confirmed_by: str,
        metadata: dict | None = None,
    ) -> FamilyRelationship:
        """Create bidirectional family relationship."""
        relationship = FamilyRelationship(
            tenant_id=tenant_id,
            client_a_id=client_a_id,
            client_b_id=client_b_id,
            relationship_type=relationship_type,
            confirmed_by=confirmed_by,
            relationship_metadata=metadata or {},
        )
        self.session.add(relationship)
        await self.session.flush()
        return relationship

    async def get_relationships_for_client(
        self, tenant_id: str, client_id: UUID
    ) -> list[FamilyRelationship]:
        """Get all relationships for a client (bidirectional)."""
        stmt = select(FamilyRelationship).where(
            FamilyRelationship.tenant_id == tenant_id,
            (FamilyRelationship.client_a_id == client_id)
            | (FamilyRelationship.client_b_id == client_id),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, tenant_id: str, relationship_id: UUID) -> bool:
        """Delete a relationship."""
        relationship = await self.get_by_id(tenant_id, relationship_id)
        if relationship:
            await self.session.delete(relationship)
            return True
        return False


class HouseholdRepository(TenantScopedRepository[HouseholdGroup]):
    """Repository for household groups with tenant isolation."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, HouseholdGroup)

    async def create_household(
        self,
        tenant_id: str,
        household_name: str,
        primary_contact_id: UUID,
        created_by: str,
        address_ref: str | None = None,
    ) -> HouseholdGroup:
        """Create a new household group."""
        household = HouseholdGroup(
            tenant_id=tenant_id,
            household_name=household_name,
            primary_contact_id=primary_contact_id,
            address_ref=address_ref,
            created_by=created_by,
        )
        self.session.add(household)
        await self.session.flush()
        return household

    async def add_member(
        self,
        tenant_id: str,
        household_id: UUID,
        client_id: UUID,
        role: str,
    ) -> HouseholdMembership:
        """Add a member to a household."""
        membership = HouseholdMembership(
            tenant_id=tenant_id,
            household_id=household_id,
            client_id=client_id,
            role=role,
        )
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def list_members(
        self, tenant_id: str, household_id: UUID
    ) -> list[HouseholdMembership]:
        """List all members of a household."""
        stmt = select(HouseholdMembership).where(
            HouseholdMembership.tenant_id == tenant_id,
            HouseholdMembership.household_id == household_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
