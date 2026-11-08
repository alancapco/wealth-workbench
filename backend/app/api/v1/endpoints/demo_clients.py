import json
from collections import defaultdict
from datetime import date, datetime, UTC
from uuid import UUID, uuid4

import httpx
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
    """Simple compound interest + monthly contribution projection as LLM fallback."""
    years = req.retirement_age - req.current_age
    r = req.assumed_annual_return_pct / 100.0
    monthly_r = r / 12.0
    months = years * 12

    fv_lump = req.current_savings_usd_millions * ((1 + r) ** years)
    if monthly_r > 0:
        fv_annuity = (req.monthly_contribution_usd / 1_000_000) * (((1 + monthly_r) ** months - 1) / monthly_r)
    else:
        fv_annuity = (req.monthly_contribution_usd / 1_000_000) * months

    projected = round(fv_lump + fv_annuity, 2)
    target = req.target_retirement_corpus_usd_millions
    gap = round(target - projected, 2)
    prob = min(100.0, max(0.0, round(100.0 * projected / target, 1))) if target > 0 else 100.0

    milestones = []
    step = max(1, years // 5)
    for yr in range(0, years + 1, step):
        fv_l = req.current_savings_usd_millions * ((1 + r) ** yr)
        m = yr * 12
        fv_a = (req.monthly_contribution_usd / 1_000_000) * (((1 + monthly_r) ** m - 1) / monthly_r) if monthly_r > 0 else (req.monthly_contribution_usd / 1_000_000) * m
        milestones.append({"year": date.today().year + yr, "age": req.current_age + yr, "corpus_usd_millions": round(fv_l + fv_a, 2)})

    recs = []
    if gap > 0:
        recs.append(f"Increase monthly contributions by USD {round(gap * 1_000_000 / max(months, 1), 0):,.0f} to bridge the gap.")
        recs.append("Consider allocating more to growth assets given the shortfall.")
    else:
        recs.append("Portfolio is on track to meet retirement target.")
        recs.append("Consider reviewing asset allocation as retirement approaches.")

    return {
        "summary": f"Based on deterministic projection at {req.assumed_annual_return_pct}% p.a., projected corpus at age {req.retirement_age} is USD {projected}M.",
        "projected_corpus_usd_millions": projected,
        "probability_of_success_pct": prob,
        "year_by_year": milestones,
        "gap_analysis": f"Gap of USD {abs(gap)}M {'below' if gap > 0 else 'above'} target.",
        "recommendations": recs,
        "_note": "LLM unavailable — deterministic compound-interest calculation used.",
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

    rates = await currency_service.get_latest_rates()

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
    report = None
    llm_error = None

    if settings.LLM_API_KEY and settings.LLM_BASE_URL:
        system_prompt = (
            "You are a financial planning assistant. Generate a retirement projection report based on the "
            "provided parameters. Include: (1) projected corpus at retirement, (2) probability of meeting target, "
            "(3) year-by-year projection table (key milestones), (4) gap analysis if target is not met, "
            "(5) recommendations. Format as structured JSON with keys: summary, projected_corpus_usd_millions, "
            "probability_of_success_pct, year_by_year (list of {year, age, corpus_usd_millions}), "
            "gap_analysis (string), recommendations (list of strings)."
        )
        user_content = json.dumps({
            "client_name": client_name,
            "current_age": req.current_age,
            "retirement_age": req.retirement_age,
            "current_savings_usd_millions": req.current_savings_usd_millions,
            "monthly_contribution_usd": req.monthly_contribution_usd,
            "target_retirement_corpus_usd_millions": req.target_retirement_corpus_usd_millions,
            "assumed_annual_return_pct": req.assumed_annual_return_pct,
            "inflation_pct": req.inflation_pct,
            "goals": [g.model_dump() for g in req.goals],
            "risk_profile": req.risk_profile,
        })
        try:
            async with httpx.AsyncClient(timeout=30) as http:
                resp = await http.post(
                    f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content},
                        ],
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                clean = content.strip()
                if clean.startswith("```"):
                    clean = "\n".join(clean.split("\n")[1:])
                    clean = clean.rsplit("```", 1)[0].strip()
                report = json.loads(clean)
        except Exception as exc:
            llm_error = str(exc)

    if report is None:
        report = _deterministic_projection(req)
        if llm_error:
            report["_llm_error"] = llm_error

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
    low, high = aum * 0.8, aum * 1.2

    peers_result = await session.execute(
        select(DemoClient)
        .options(selectinload(DemoClient.portfolio_holdings))
        .where(
            DemoClient.is_active == True,
            DemoClient.id != client_id,
            DemoClient.risk_profile == client.risk_profile,
            DemoClient.aum_usd_millions >= low,
            DemoClient.aum_usd_millions <= high,
        )
    )
    peers = peers_result.scalars().all()

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
