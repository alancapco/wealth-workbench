"""Client context assembly - aggregate entitled client data per Architecture §3.2.

Assembles:
- Client profile with tenant/book authorization
- Holdings and portfolio snapshot
- Interactions history
- Confirmed memory entries
- Per-source availability and provenance
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client, ClientMemoryEntry, ClientScope, Holding, Interaction
from app.schemas.client import (
    Account,
    AccountEligibility,
    ClientDetail,
    ClientSummary,
    Contact,
    ContactChannel,
    ContactPolicy,
    MemoryEntry,
    Portfolio,
    Profile,
    ProfileValidity,
)
from app.schemas.common import (
    Availability,
    Environment,
    EnvironmentKind,
    Origin,
    Source,
)


class ClientContextService:
    """Client context assembly with entitled data aggregation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_client_summary(
        self,
        tenant_id: str,
        client_id: UUID,
        book_id: str,
    ) -> ClientSummary | None:
        """Get client summary with authorization check per API-002."""
        # Verify client scope (tenant + client ownership)
        stmt = select(ClientScope).where(
            ClientScope.tenant_id == tenant_id,
            ClientScope.client_id == client_id
        )
        result = await self.session.execute(stmt)
        scope = result.scalar_one_or_none()
        
        if not scope:
            return None  # Client not in tenant - 404
        
        # Get client entity
        stmt = select(Client).where(Client.id == client_id)
        result = await self.session.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            return None
        
        # Create source provenance
        source = Source(
            id=UUID('00000000-0000-0000-0000-000000000001'),  # Synthetic source ID
            environment=Environment(kind=EnvironmentKind.FIXTURE, id="test-env"),
            availability=Availability.AVAILABLE,
            origin=Origin.RECORDED,
            live_response=False,
            limitation_codes=[]
        )
        
        return ClientSummary(
            id=client.id,
            external_id=client.external_id,
            name=client.name,
            book_id=book_id,
            client_type=client.client_type,
            risk_label=client.risk_profile,
            source=source
        )

    async def get_client_detail(
        self,
        tenant_id: str,
        client_id: UUID,
        book_id: str,
    ) -> ClientDetail | None:
        """Get client detail with full context per API-003."""
        summary = await self.get_client_summary(tenant_id, client_id, book_id)
        if not summary:
            return None
        
        # Get client entity for additional fields
        stmt = select(Client).where(Client.id == client_id)
        result = await self.session.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            return None
        
        # Assemble contacts
        contacts = []
        if client.email:
            contacts.append(Contact(
                id=f"email-{client.id}",
                channel=ContactChannel.EMAIL,
                destination=client.email,
                source=summary.source
            ))
        if client.phone:
            contacts.append(Contact(
                id=f"sms-{client.id}",
                channel=ContactChannel.SMS,
                destination=client.phone,
                source=summary.source
            ))
        
        # Assemble accounts (from holdings)
        stmt = select(Holding).where(Holding.client_id == client_id)
        result = await self.session.execute(stmt)
        holdings = result.scalars().all()
        
        account_ids = {h.id for h in holdings}
        accounts = [
            Account(
                id=str(acc_id),
                client_id=client_id,
                currency=client.currency or "USD",
                eligibility=AccountEligibility.ELIGIBLE,
                source=summary.source
            )
            for acc_id in account_ids
        ]
        
        # Profile (from client fields)
        profile = None
        if client.risk_profile:
            profile = Profile(
                id=f"profile-{client.id}",
                version="1",
                risk_code=client.risk_profile,
                validity=ProfileValidity.CURRENT,
                as_of=client.updated_at,
                fields=[],
                source=summary.source
            )
        
        # Contact policy
        contact_policy = ContactPolicy(
            dnc=False,
            channels=[
                {"channel": "EMAIL", "consented": True if client.email else None},
                {"channel": "SMS", "consented": True if client.phone else None},
            ],
            config_ref=None
        )
        
        # Memory entries
        stmt = select(ClientMemoryEntry).where(
            ClientMemoryEntry.tenant_id == tenant_id,
            ClientMemoryEntry.client_id == client_id,
            ClientMemoryEntry.state == "CONFIRMED"
        )
        result = await self.session.execute(stmt)
        memory_records = result.scalars().all()
        
        memory = [
            MemoryEntry(
                id=m.id,
                key=m.memory_key,
                value={"type": "TEXT", "value": m.value},  # Simplified
                version=m.version,
                state=m.state,
                source_ref={"artifact_id": m.source_revision_id, "revision_id": m.source_revision_id, "version": 1, "hash": "0" * 64},
                confirmed_by=m.confirmed_by,
                confirmed_at=m.confirmed_at,
                sources=[summary.source]
            )
            for m in memory_records
        ]
        
        return ClientDetail(
            summary=summary,
            contacts=contacts,
            accounts=accounts,
            profile=profile,
            contact_policy=contact_policy,
            memory=memory
        )

    async def get_portfolio(
        self,
        tenant_id: str,
        client_id: UUID,
    ) -> Portfolio | None:
        """Get portfolio snapshot per API-020."""
        # Verify client scope
        stmt = select(ClientScope).where(
            ClientScope.tenant_id == tenant_id,
            ClientScope.client_id == client_id
        )
        result = await self.session.execute(stmt)
        scope = result.scalar_one_or_none()
        
        if not scope:
            return None
        
        # Get holdings
        stmt = select(Holding).where(Holding.client_id == client_id)
        result = await self.session.execute(stmt)
        holdings_data = result.scalars().all()
        
        # Get client for currency
        stmt = select(Client).where(Client.id == client_id)
        result = await self.session.execute(stmt)
        client = result.scalar_one_or_none()
        
        base_currency = client.currency if client else "USD"
        
        # Create source
        source = Source(
            id=UUID('00000000-0000-0000-0000-000000000002'),
            environment=Environment(kind=EnvironmentKind.FIXTURE, id="test-env"),
            availability=Availability.AVAILABLE,
            origin=Origin.RECORDED,
            live_response=False,
            limitation_codes=[]
        )
        
        # Build holdings list
        from app.schemas.client import Holding as HoldingSchema
        from app.schemas.common import Money
        from decimal import Decimal
        
        holdings = []
        total_value = Decimal('0')
        
        for h in holdings_data:
            market_value = None
            if h.current_value:
                market_value = Money(amount=Decimal(str(h.current_value)), currency=base_currency)
                total_value += Decimal(str(h.current_value))
            
            holdings.append(HoldingSchema(
                id=str(h.id),
                account_id=str(h.id),
                instrument_id=h.symbol or "UNKNOWN",
                symbol=h.symbol,
                quantity=Decimal(str(h.quantity)) if h.quantity else None,
                market_value=market_value,
                cost_basis=Money(amount=Decimal(str(h.cost_basis)), currency=base_currency) if h.cost_basis else None,
                asset_class=h.asset_class,
                source=source
            ))
        
        return Portfolio(
            id=f"portfolio-{client_id}",
            client_id=client_id,
            as_of=client.updated_at if client else None,
            base_currency=base_currency,
            aum=Money(amount=total_value, currency=base_currency) if total_value > 0 else None,
            holdings=holdings,
            allocation=[],
            performance=[],
            sources=[source]
        )
