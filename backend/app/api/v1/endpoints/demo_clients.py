from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from datetime import datetime, UTC

from app.core.database import get_db
from app.models.client_data import (
    ClientConversation,
    ClientFinancialPlan,
    ClientPortfolioHolding,
    DemoClient,
)

router = APIRouter(prefix="/demo-clients", tags=["demo-clients"])


@router.get("")
async def list_demo_clients(
    tag: str = Query("capcodemo"),
    segment: str = Query(None),
    session: AsyncSession = Depends(get_db),
):
    query = select(DemoClient).where(DemoClient.tag == tag, DemoClient.is_active == True)
    if segment:
        query = query.where(DemoClient.client_segment == segment)
    clients = (await session.execute(query)).scalars().all()
    return {
        "data": {
            "clients": [
                {
                    "id": str(c.id),
                    "name": f"{c.firstname} {c.lastname}",
                    "email": c.email,
                    "city": c.city,
                    "country": c.country,
                    "aum_usd_millions": c.aum_usd_millions,
                    "client_segment": c.client_segment,
                    "portfolio_type": c.portfolio_type,
                    "risk_profile": c.risk_profile,
                    "shariah_compliant": c.shariah_compliant,
                    "family_office_name": c.family_office_name,
                    "family_role": c.family_role,
                    "ethnicity": c.ethnicity,
                    "religion": c.religion,
                }
                for c in clients
            ],
            "count": len(clients),
        },
        "meta": {"request_id": str(uuid4()), "served_at": datetime.now(UTC).isoformat()},
    }


@router.get("/{client_id}")
async def get_demo_client_detail(
    client_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    client = (
        await session.execute(select(DemoClient).where(DemoClient.id == client_id))
    ).scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client not found")

    holdings = (
        await session.execute(
            select(ClientPortfolioHolding).where(ClientPortfolioHolding.client_id == client_id)
        )
    ).scalars().all()

    plans = (
        await session.execute(
            select(ClientFinancialPlan).where(ClientFinancialPlan.client_id == client_id)
        )
    ).scalars().all()

    convs = (
        await session.execute(
            select(ClientConversation)
            .where(ClientConversation.client_id == client_id)
            .order_by(ClientConversation.conversation_date.desc())
        )
    ).scalars().all()

    return {
        "data": {
            "client": {
                "id": str(client.id),
                "name": f"{client.firstname} {client.lastname}",
                "email": client.email,
                "phone": client.phone,
                "city": client.city,
                "country": client.country,
                "ethnicity": client.ethnicity,
                "religion": client.religion,
                "aum_usd_millions": client.aum_usd_millions,
                "client_segment": client.client_segment,
                "risk_profile": client.risk_profile,
                "portfolio_type": client.portfolio_type,
                "shariah_compliant": client.shariah_compliant,
                "family_office_name": client.family_office_name,
                "family_role": client.family_role,
            },
            "portfolio": [
                {
                    "asset_class": h.asset_class,
                    "asset_name": h.asset_name,
                    "ticker": h.ticker,
                    "value_usd_millions": h.value_usd_millions,
                    "allocation_pct": h.allocation_pct,
                    "unrealized_gain_pct": h.unrealized_gain_pct,
                    "currency": h.currency,
                    "is_shariah_compliant": h.is_shariah_compliant,
                }
                for h in holdings
            ],
            "financial_plans": [
                {
                    "plan_type": p.plan_type,
                    "goal_description": p.goal_description,
                    "target_amount_usd_millions": p.target_amount_usd_millions,
                    "target_date": p.target_date.isoformat() if p.target_date else None,
                    "current_progress_pct": p.current_progress_pct,
                    "status": p.status,
                    "notes": p.notes,
                }
                for p in plans
            ],
            "recent_conversations": [
                {
                    "date": c.conversation_date.isoformat(),
                    "channel": c.channel,
                    "summary": c.summary,
                    "sentiment": c.sentiment,
                    "action_items": c.action_items,
                    "next_steps": c.next_steps,
                }
                for c in convs
            ],
        },
        "meta": {"request_id": str(uuid4()), "served_at": datetime.now(UTC).isoformat()},
    }
