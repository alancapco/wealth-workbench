import json
from collections import defaultdict
from datetime import date, datetime, UTC
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.client_data import (
    ClientConversation,
    ClientFinancialPlan,
    ClientPortfolioHolding,
    ClientSuitabilityProfile,
    DemoClient,
)
from app.services.market.currency_service import currency_service

router = APIRouter(prefix="/demo-clients", tags=["demo-clients"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class GoalRequest(BaseModel):
    name: str
    target_amount_usd_millions: float
    target_year: int


class FuturePlannerRequest(BaseModel):
    current_age: int
    retirement_age: int
    current_savings_usd_millions: float
    monthly_contribution_usd: float = 0.0
    target_retirement_corpus_usd_millions: float
    assumed_annual_return_pct: float = 6.0
    inflation_pct: float = 2.5
    goals: list[GoalRequest] = []
    risk_profile: str = "Moderate"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deterministic_projection(req: FuturePlannerRequest) -> dict:
    """Compound interest + monthly contributions. The model does not compute these figures."""
    from app.services.planning.projection import project_plan

    report = project_plan(
        current_age=req.current_age,
        retirement_age=req.retirement_age,
        current_savings_usd_millions=req.current_savings_usd_millions,
        monthly_contribution_usd=req.monthly_contribution_usd,
        target_retirement_corpus_usd_millions=req.target_retirement_corpus_usd_millions,
        assumed_annual_return_pct=req.assumed_annual_return_pct,
        inflation_pct=req.inflation_pct,
    )
    report["_note"] = "Deterministic compound-interest calculation. Narrative, when present, does not change the figures."
    return report


async def _plan_narrative(client_name: str, report: dict, risk_profile: str) -> dict:
    """The model explains the figures. It is not allowed to replace them."""
    from app.services.journey.llm import complete_json

    base = {
        "executive_narrative": report["summary"],
        "projection_source": "deterministic",
        "model": None,
        "actionable_levers": report["recommendations"],
    }
    raw = await complete_json(
        "Explain this retirement illustration for a relationship manager. "
        "Do not change any number. Reply with JSON keys executive_narrative (string) and actionable_levers (list of strings).",
        json.dumps({
            "client_name": client_name,
            "risk_profile": risk_profile,
            "summary": report["summary"],
            "projected_corpus_usd_millions": report["projected_corpus_usd_millions"],
            "real_projected_corpus_usd_millions": report["real_projected_corpus_usd_millions"],
            "gap_analysis": report["gap_analysis"],
            "scenarios": {
                key: value["projected_corpus_usd_millions"]
                for key, value in report.get("scenarios", {}).items()
            },
        }),
        timeout_s=20,
    )
    if not isinstance(raw, dict) or not isinstance(raw.get("executive_narrative"), str):
        return base
    levers = [str(item) for item in raw.get("actionable_levers") or [] if str(item).strip()]
    return {
        "executive_narrative": raw["executive_narrative"].strip(),
        "projection_source": "llm",
        "model": settings.LLM_MODEL,
        "actionable_levers": levers or report["recommendations"],
    }


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

    suitability = (
        await session.execute(
            select(ClientSuitabilityProfile).where(ClientSuitabilityProfile.client_id == client_id)
        )
    ).scalar_one_or_none()

    return {
        "data": {
            "client": {
                "id": str(client.id),
                "firstname": client.firstname,
                "lastname": client.lastname,
                "full_name": f"{client.firstname} {client.lastname}",
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
                "holdings_count": len(holdings),
                "total_holdings_value_usd_millions": round(sum(h.value_usd_millions or 0.0 for h in holdings), 4),
            },
            "portfolio_holdings": [
                {
                    "id": str(h.id),
                    "asset_class": h.asset_class,
                    "asset_name": h.asset_name,
                    "ticker": h.ticker,
                    "value_usd_millions": h.value_usd_millions,
                    "allocation_pct": h.allocation_pct,
                    "unrealized_gain_pct": h.unrealized_gain_pct,
                    "currency": h.currency,
                    "is_shariah_compliant": h.is_shariah_compliant,
                    "as_of_date": h.as_of_date.isoformat() if h.as_of_date else None,
                }
                for h in holdings
            ],
            "financial_plans": [
                {
                    "id": str(p.id),
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
            "conversations": [
                {
                    "id": str(c.id),
                    "conversation_date": c.conversation_date.isoformat(),
                    "channel": c.channel,
                    "summary": c.summary,
                    "sentiment": c.sentiment,
                    "action_items": c.action_items,
                    "next_steps": c.next_steps,
                }
                for c in convs
            ],
            "suitability_profile": {
                "risk_tolerance": suitability.risk_tolerance,
                "investment_horizon_years": suitability.investment_horizon_years,
                "liquidity_needs": suitability.liquidity_needs,
                "esg_preference": suitability.esg_preference,
                "shariah_preference": suitability.shariah_preference,
                "max_single_stock_pct": suitability.max_single_stock_pct,
                "profile_date": suitability.profile_date.isoformat() if suitability.profile_date else None,
                "is_expired": suitability.is_expired,
            } if suitability else None,
        },
        "meta": {"request_id": str(uuid4()), "served_at": datetime.now(UTC).isoformat()},
    }


@router.get("/{client_id}/portfolio/currency-exposure")
async def get_currency_exposure(
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

    rates_info = await currency_service.get_latest_rates_with_metadata()
    rates = rates_info["rates"]

    by_currency: dict[str, dict] = defaultdict(lambda: {"value_usd_millions": 0.0, "count": 0})
    total_usd = 0.0
    for h in holdings:
        cur = h.currency or "USD"
        val = h.value_usd_millions or 0.0
        by_currency[cur]["value_usd_millions"] += val
        by_currency[cur]["count"] += 1
        total_usd += val

    breakdown = []
    for cur, agg in by_currency.items():
        fx_rate = rates.get(cur, 1.0)
        val_usd = agg["value_usd_millions"]
        breakdown.append({
            "currency": cur,
            "value_in_currency_millions": round(val_usd * fx_rate, 4),
            "value_usd_millions": round(val_usd, 4),
            "allocation_pct": round(val_usd / total_usd * 100, 2) if total_usd else 0.0,
            "fx_rate": fx_rate,
            "holdings_count": agg["count"],
        })
    breakdown.sort(key=lambda x: x["value_usd_millions"], reverse=True)

    used_currencies = list(by_currency.keys()) + ["USD"]
    rates_used = {k: v for k, v in rates.items() if k in used_currencies}

    return {
        "data": {
            "client_id": str(client_id),
            "client_name": f"{client.firstname} {client.lastname}",
            "base_currency": "USD",
            "as_of_date": str(date.today()),
            "total_value_usd_millions": round(total_usd, 4),
            "currency_breakdown": breakdown,
            "rates_used": rates_used,
            "rates_source": rates_info["source"],
            "rates_as_of": rates_info["as_of"],
            "rates_is_live": rates_info["is_live"],
            "rates_note": rates_info["note"],
        },
        "meta": {},
    }


@router.get("/{client_id}/portfolio/asset-class-breakdown")
async def get_asset_class_breakdown(
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

    total_usd = sum(h.value_usd_millions or 0.0 for h in holdings)
    by_class: dict[str, dict] = defaultdict(lambda: {"value_usd_millions": 0.0, "holdings": []})
    for h in holdings:
        ac = h.asset_class or "Other"
        by_class[ac]["value_usd_millions"] += h.value_usd_millions or 0.0
        by_class[ac]["holdings"].append({
            "asset_name": h.asset_name,
            "ticker": h.ticker,
            "value_usd_millions": h.value_usd_millions,
            "currency": h.currency,
            "unrealized_gain_pct": h.unrealized_gain_pct,
        })

    breakdown = []
    for ac, agg in by_class.items():
        val = agg["value_usd_millions"]
        breakdown.append({
            "asset_class": ac,
            "value_usd_millions": round(val, 4),
            "allocation_pct": round(val / total_usd * 100, 2) if total_usd else 0.0,
            "holdings_count": len(agg["holdings"]),
            "holdings": agg["holdings"],
        })
    breakdown.sort(key=lambda x: x["value_usd_millions"], reverse=True)

    return {
        "data": {
            "client_id": str(client_id),
            "client_name": f"{client.firstname} {client.lastname}",
            "total_value_usd_millions": round(total_usd, 4),
            "asset_class_breakdown": breakdown,
        },
        "meta": {},
    }


@router.post("/{client_id}/future-planner")
async def future_planner(
    client_id: UUID,
    req: FuturePlannerRequest,
    session: AsyncSession = Depends(get_db),
):
    client = (
        await session.execute(select(DemoClient).where(DemoClient.id == client_id))
    ).scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client not found")

    client_name = f"{client.firstname} {client.lastname}"
    report = _deterministic_projection(req)
    narrative = await _plan_narrative(client_name, report, req.risk_profile)
    report.update(narrative)

    return {
        "data": {
            "client_id": str(client_id),
            "client_name": client_name,
            "report": report,
            "disclaimer": "This is an AI-generated projection for demonstration purposes only. Not financial advice.",
        },
        "meta": {},
    }


@router.get("/{client_id}/investors-like-me")
async def investors_like_me(
    client_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    client = (
        await session.execute(select(DemoClient).where(DemoClient.id == client_id))
    ).scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client not found")

    aum = client.aum_usd_millions or 0.0
    # Broaden: ±50% AUM range to ensure enough peers in a small demo dataset
    low, high = aum * 0.5, aum * 1.5

    # Adjacent risk profiles: Moderate matches Conservative and Balanced too
    ADJACENT_RISK: dict[str, list[str]] = {
        "Conservative": ["Conservative", "Moderate"],
        "Moderate": ["Conservative", "Moderate", "Balanced"],
        "Balanced": ["Moderate", "Balanced", "Aggressive"],
        "Aggressive": ["Balanced", "Aggressive"],
    }
    risk_group = ADJACENT_RISK.get(client.risk_profile or "Moderate", [client.risk_profile])

    peers_result = await session.execute(
        select(DemoClient)
        .options(selectinload(DemoClient.portfolio_holdings))
        .where(
            DemoClient.is_active == True,
            DemoClient.id != client_id,
            DemoClient.risk_profile.in_(risk_group),
            DemoClient.aum_usd_millions >= low,
            DemoClient.aum_usd_millions <= high,
        )
    )
    peers = peers_result.scalars().all()
    # If still too few, fall back to same risk profile only, no AUM filter
    if len(peers) < 2:
        fallback_result = await session.execute(
            select(DemoClient)
            .options(selectinload(DemoClient.portfolio_holdings))
            .where(
                DemoClient.is_active == True,
                DemoClient.id != client_id,
                DemoClient.risk_profile.in_(risk_group),
            )
        )
        peers = fallback_result.scalars().all()

    my_holdings = (
        await session.execute(
            select(ClientPortfolioHolding).where(ClientPortfolioHolding.client_id == client_id)
        )
    ).scalars().all()

    my_total = sum(h.value_usd_millions or 0.0 for h in my_holdings)
    my_by_class: dict[str, float] = defaultdict(float)
    for h in my_holdings:
        my_by_class[h.asset_class or "Other"] += h.value_usd_millions or 0.0

    your_allocation = [
        {"asset_class": ac, "allocation_pct": round(val / my_total * 100, 2) if my_total else 0.0}
        for ac, val in sorted(my_by_class.items(), key=lambda x: -x[1])
    ]

    all_asset_classes = set(my_by_class.keys())
    peer_class_vals: dict[str, float] = defaultdict(float)
    peer_total_aum = 0.0
    for peer in peers:
        for h in peer.portfolio_holdings:
            ac = h.asset_class or "Other"
            all_asset_classes.add(ac)
            peer_class_vals[ac] += h.value_usd_millions or 0.0
            peer_total_aum += h.value_usd_millions or 0.0

    peer_avg_allocation = []
    if peers:
        for ac in sorted(all_asset_classes):
            avg_pct = round(peer_class_vals.get(ac, 0.0) / peer_total_aum * 100, 2) if peer_total_aum else 0.0
            peer_avg_allocation.append({"asset_class": ac, "allocation_pct": avg_pct})
        peer_avg_allocation.sort(key=lambda x: -x["allocation_pct"])

    my_map = {x["asset_class"]: x["allocation_pct"] for x in your_allocation}
    peer_map = {x["asset_class"]: x["allocation_pct"] for x in peer_avg_allocation}
    notes = []
    for ac in all_asset_classes:
        diff = round(my_map.get(ac, 0.0) - peer_map.get(ac, 0.0), 1)
        if abs(diff) >= 3.0:
            direction = "more" if diff > 0 else "less"
            notes.append(f"You are {abs(diff)}% {direction} allocated to {ac} than peers with similar profiles")

    if not notes:
        notes.append("Your asset allocation is broadly in line with similar peers.")

    return {
        "data": {
            "client_id": str(client_id),
            "client_name": f"{client.firstname} {client.lastname}",
            "your_allocation": your_allocation,
            "peer_avg_allocation": peer_avg_allocation,
            "peer_count": len(peers),
            "comparison_notes": notes,
        },
        "meta": {},
    }
