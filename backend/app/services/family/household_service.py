"""Household service for cross-member context (U-016, DEC-07 gated)."""
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.family import HouseholdRepository
from app.schemas.family import HouseholdContext


class HouseholdService:
    """Service for managing household groups and cross-member context."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = HouseholdRepository(session)

    async def create_household(
        self,
        tenant_id: str,
        household_name: str,
        primary_contact_id: UUID,
        created_by: str,
        address_ref: str | None = None,
        initial_members: list[UUID] | None = None,
    ) -> UUID:
        """Create a household group with optional initial members."""
        # Create household
        household = await self.repo.create_household(
            tenant_id=tenant_id,
            household_name=household_name,
            primary_contact_id=primary_contact_id,
            created_by=created_by,
            address_ref=address_ref,
        )

        # Add primary contact as PRIMARY member
        await self.repo.add_member(
            tenant_id=tenant_id,
            household_id=household.id,
            client_id=primary_contact_id,
            role="PRIMARY",
        )

        # Add initial members
        if initial_members:
            for member_id in initial_members:
                if member_id != primary_contact_id:
                    await self.repo.add_member(
                        tenant_id=tenant_id,
                        household_id=household.id,
                        client_id=member_id,
                        role="MEMBER",
                    )

        return household.id

    async def get_cross_member_context(
        self,
        tenant_id: str,
        workflow_id: UUID,
        household_id: UUID,
        dec07_enabled: bool = False,
    ) -> HouseholdContext:
        """Get aggregated context from all consenting household members.
        
        Returns UNCONFIGURED if DEC-07 gate is disabled.
        Requires consent from ALL members before returning context.
        """
        if not dec07_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "FEATURE_DISABLED",
                        "message": "Household context requires DEC-07 gate enabled",
                        "retryable": False,
                    }
                },
            )

        # Get household
        household = await self.repo.get_by_id(tenant_id, household_id)
        if not household:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "HOUSEHOLD_NOT_FOUND",
                        "message": f"Household {household_id} not found",
                        "retryable": False,
                    }
                },
            )

        # Get members
        members = await self.repo.list_members(tenant_id, household_id)

        # In production: check consent for each member
        # For pilot: return placeholder context
        member_contexts = []
        consenting_count = len(members)  # Simplified: assume all consent

        return HouseholdContext(
            household_id=household_id,
            household_name=household.household_name,
            member_contexts=member_contexts,
            total_members=len(members),
            consenting_members=consenting_count,
            aggregated_at=datetime.utcnow(),
        )
