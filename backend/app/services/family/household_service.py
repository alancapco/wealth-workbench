"""Household service for cross-member context (U-016, DEC-07 gated)."""
from datetime import datetime, UTC
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client, Holding
from app.models.capture import ConsentRecord
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

    async def _has_valid_consent(self, tenant_id: str, client_id: UUID) -> bool:
        """Consent must be an active, non-withdrawn ACCEPTED record; missing = no consent."""
        try:
            stmt = select(ConsentRecord.id).where(
                ConsentRecord.tenant_id == tenant_id,
                ConsentRecord.client_id == client_id,
                ConsentRecord.state == "ACCEPTED",
                ConsentRecord.withdrawn_at.is_(None),
            )
            return (await self.session.execute(stmt)).first() is not None
        except Exception:
            # Fail closed: an unverifiable consent state is not consent.
            return False

    async def _member_context(self, member) -> dict:
        """Context assembled from the member's real client and holding records."""
        client = (
            await self.session.execute(select(Client).where(Client.id == member.client_id))
        ).scalar_one_or_none()
        if client is None:
            return {"client_id": str(member.client_id), "role": member.role, "availability": "UNAVAILABLE"}

        holdings = (
            await self.session.execute(select(Holding).where(Holding.client_id == member.client_id))
        ).scalars().all()
        return {
            "client_id": str(member.client_id),
            "role": member.role,
            "name": client.name,
            "risk_profile": client.risk_profile,
            "aum": client.aum,
            "currency": client.currency,
            "holdings_count": len(holdings),
            "total_holdings_value": round(sum(h.current_value or 0 for h in holdings), 4),
        }

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

        consented = [
            member for member in members
            if await self._has_valid_consent(tenant_id, member.client_id)
        ]

        # Fail closed: cross-member context is exposed only when every member
        # has a verifiable consent record; a partial household returns no context.
        member_contexts = []
        if len(consented) == len(members):
            member_contexts = [await self._member_context(member) for member in consented]

        return HouseholdContext(
            household_id=household_id,
            household_name=household.household_name,
            member_contexts=member_contexts,
            total_members=len(members),
            consenting_members=len(consented),
            aggregated_at=datetime.now(UTC),
        )
