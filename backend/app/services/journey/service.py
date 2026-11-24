"""Database operations for the five-stage wealth journey."""
from __future__ import annotations

import hashlib
import json
import csv
from datetime import date, datetime, UTC
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_data import ClientConversation, ClientPortfolioHolding, DemoClient
from app.models.journey import (
    JourneyApproval,
    JourneyCart,
    JourneyCartItem,
    JourneyCohort,
    JourneyDocument,
    JourneyEvent,
    JourneyFinancialProfile,
    JourneyGoal,
    JourneyHandoff,
    JourneyInvestorProfile,
    JourneyLeadControl,
    JourneyNotification,
    JourneyOpportunity,
    JourneySignal,
    JourneyTransaction,
)
from app.services.journey.logic import (
    CATALOGUE,
    FINANCIAL_PROFILE_FIELDS,
    PIPELINE_STAGES,
    assess_product,
    auto_approval,
    default_expiry,
    drift_vs_saa,
    extract_profile_updates,
    jurisdiction_code,
    next_stage,
    optimise,
    pitch,
    protect_answer,
    score_lead,
    stress,
)

MAKER = "fixture:rm001@example.test"


def _pack_path() -> Path:
    return Path(__file__).resolve().parents[4] / "demo_data" / "clients.csv"


async def _load_demo_pack(db: AsyncSession) -> list[DemoClient]:
    path = _pack_path()
    if not path.exists():
        return []
    created: list[DemoClient] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("display_name") or "Demo Client").strip()
            parts = name.split()
            first = parts[0]
            last = " ".join(parts[1:]) or "Client"
            email = row.get("contact_email") or f"{row.get('client_id', name)}@demo.invalid"
            try:
                aum = float(row.get("aum_sgd") or 0) / 1_000_000
            except ValueError:
                aum = 0
            client = DemoClient(
                firstname=first[:100],
                lastname=last[:100],
                email=email[:255],
                country=(row.get("jurisdiction") or "Singapore")[:100],
                aum_usd_millions=round(aum, 2),
                client_segment=(row.get("segment") or "HNW")[:50],
                risk_profile="Moderate",
                shariah_compliant=str(row.get("shariah_sensitive")).lower() == "true",
                tag="journey-pack",
            )
            db.add(client)
            created.append(client)
    await db.commit()
    return created


def _client_name(client: DemoClient) -> str:
    return f"{client.firstname} {client.lastname}".strip()


async def record_event(db: AsyncSession, stage: str, event: str, client_id=None, detail=None, actor=MAKER):
    row = JourneyEvent(
        stage=stage,
        event=event,
        client_id=client_id,
        actor=actor,
        detail=detail or {},
    )
    db.add(row)
    return row


async def ensure_seeded(db: AsyncSession) -> int:
    """Overlay journey records on the demo-client book. Idempotent.

    An empty book is filled from demo_data/clients.csv (the SG-heavy pack)
    so Engage is not a blank screen on a fresh database.
    """
    clients = (await db.execute(select(DemoClient))).scalars().all()
    if not clients:
        clients = await _load_demo_pack(db)
    if not clients:
        return 0
    existing = (await db.execute(select(JourneyInvestorProfile.client_id))).scalars().all()
    have = set(existing)
    created = 0
    today = date.today()
    for index, client in enumerate(clients):
        if client.id in have:
            continue
        code = jurisdiction_code(client.country)
        expired = index % 5 == 1
        expiry = today.replace(year=today.year - 1) if expired else default_expiry(today, 20 if index % 4 == 0 else 400)
        vulnerable = index % 7 == 0
        hrs = index % 11 == 0
        db.add(JourneyInvestorProfile(
            client_id=client.id,
            rpq_band=client.risk_profile or "Moderate",
            rpq_score=60,
            rpq_answers={"source": "SYNTHETIC_DEMO_DATA"},
            cka_passed=not (index % 6 == 0),
            car_status="CURRENT",
            investor_status="ACCREDITED" if (client.aum_usd_millions or 0) >= 5 else "RETAIL",
            accreditation_evidence="demo-pack" if (client.aum_usd_millions or 0) >= 5 else None,
            expiry_date=expiry,
            vulnerable=vulnerable,
            high_risk_segment=hrs,
            cross_border_restricted=code == "HK" and index % 9 == 0,
        ))
        db.add(JourneyFinancialProfile(
            client_id=client.id,
            annual_income_band="1M-5M",
            investable_assets_band="5M+",
            liquidity_need="MEDIUM",
            investment_objective=client.portfolio_type or "Growth",
            version=1,
        ))
        db.add(JourneyGoal(
            client_id=client.id,
            name="Retirement",
            target_usd=(client.aum_usd_millions or 1) * 1_200_000,
            target_date=date(today.year + 12, 1, 1),
            monthly_contribution_usd=20000,
            current_usd=(client.aum_usd_millions or 1) * 400_000,
            status="OPEN",
            product_tags=[],
        ))
        if expired or (index % 4 == 0):
            db.add(JourneySignal(
                client_id=client.id,
                kind="RPQ_EXPIRY",
                summary="RPQ expires inside 30 days" if not expired else "RPQ is expired",
                source="investor-profile",
                as_of=today,
            ))
        if index % 3 == 0:
            db.add(JourneySignal(
                client_id=client.id,
                kind="SAA_DRIFT",
                summary="Allocation is away from the CIO SAA",
                source="portfolio",
                as_of=today,
            ))
        db.add(JourneyOpportunity(
            client_id=client.id,
            title=f"Review {_client_name(client)}",
            stage="ACTIONABLE",
            source="SIGNAL",
            value_usd=(client.aum_usd_millions or 1) * 50_000,
            probability_pct=30,
        ))
        db.add(JourneyTransaction(
            client_id=client.id,
            trade_date=today,
            txn_type="BUY",
            description="Synthetic opening position",
            amount_usd=(client.aum_usd_millions or 1) * 100_000,
            currency="USD",
            source="SYNTHETIC_DEMO_DATA",
        ))
        created += 1
    if created:
        await record_event(db, "PLT", "seed", detail={"clients": created})
        await db.commit()
    await enrich_records(db)
    return created


def _bands(aum: float) -> tuple[str, str, str]:
    if aum >= 80:
        return "5M+", "100M+", "LOW"
    if aum >= 30:
        return "1M-5M", "20M-50M", "MEDIUM"
    return "500K-1M", "5M-20M", "HIGH"


# Per-client story. Ahmad Rahman and Tan Family Office are separate households.
CLIENT_STORIES = {
    "ahmad.rahman@capcodemo.com": {
        "income": "1M-5M",
        "assets": "20M-50M",
        "liquidity": "MEDIUM",
        "objective": "Capital preservation, Shariah",
        "goals": [
            ("Children's education 2031", 4_000_000, 1_200_000),
            ("SGD capital reserve", 8_000_000, 6_000_000),
        ],
        "documents": [
            ("KYC", "ahmad-rahman-kyc.pdf", "Identity and address, current"),
            ("TAX_FORM", "ahmad-rpq-signed.pdf", "Conservative RPQ, AAOIFI preference"),
        ],
        "transactions": [
            ("BUY", "Malaysia Sukuk 5Y", 2_400_000),
            ("BUY", "SGD Murabahah deposit top-up", 500_000),
            ("DIVIDEND", "Sabana REIT distribution", 42_000),
        ],
        "conversation": "Confirmed the book stays AAOIFI compliant. No link to any family office.",
    },
    "office@tanfamilyoffice.capcodemo.com": {
        "income": "5M+",
        "assets": "100M+",
        "liquidity": "LOW",
        "objective": "Multi-entity growth and succession",
        "goals": [
            ("Operating company succession 2028", 40_000_000, 18_000_000),
            ("Gen-3 education trusts", 12_000_000, 7_500_000),
        ],
        "documents": [
            ("CONTRACT", "tan-family-charter.pdf", "Tan household only. Not related to Ahmad Rahman."),
            ("KYC", "tan-patriarch-trust-kyc.pdf", "Patriarch Trust and operating company"),
        ],
        "transactions": [
            ("BUY", "CapitaLand REIT addition", 1_500_000),
            ("BUY", "KKR infrastructure call", 2_000_000),
            ("FEE", "Family office administration", 180_000),
        ],
        "conversation": "Reviewed the Tan charter and the two education trusts. Ahmad Rahman is a separate client.",
    },
}


async def enrich_records(db: AsyncSession) -> int:
    """Fill goals, documents, transactions and a conversation where the row is still a stub."""
    clients = (await db.execute(select(DemoClient))).scalars().all()
    filled = 0
    today = date.today()
    for client in clients:
        docs = (await db.execute(
            select(JourneyDocument.id).where(JourneyDocument.client_id == client.id).limit(1)
        )).first()
        if docs is not None:
            continue
        story = CLIENT_STORIES.get(client.email or "")
        aum = float(client.aum_usd_millions or 1)
        income, assets, liquidity = _bands(aum)
        objective = client.portfolio_type or "Growth"
        goals = [("Retirement", aum * 1_200_000, aum * 400_000), ("Liquidity reserve", aum * 150_000, aum * 80_000)]
        documents = [
            ("KYC", f"{client.firstname}-{client.lastname}-kyc.pdf".replace(" ", "-").lower(), "Current identity pack"),
            ("STATEMENT", f"{client.firstname}-statement.pdf".replace(" ", "-").lower(), "Latest custody statement"),
        ]
        transactions = [
            ("BUY", f"Opening position in {client.portfolio_type or 'portfolio'}", aum * 200_000),
            ("DIVIDEND", "Cash distribution", aum * 4_000),
        ]
        conversation = f"Review with {client.firstname} {client.lastname}. Separate household."
        if story:
            income, assets, liquidity = story["income"], story["assets"], story["liquidity"]
            objective = story["objective"]
            goals = story["goals"]
            documents = story["documents"]
            transactions = story["transactions"]
            conversation = story["conversation"]
        financial = await db.get(JourneyFinancialProfile, client.id)
        if financial:
            financial.annual_income_band = income
            financial.investable_assets_band = assets
            financial.liquidity_need = liquidity
            financial.investment_objective = objective
        existing_goals = (await db.execute(select(JourneyGoal).where(JourneyGoal.client_id == client.id))).scalars().all()
        if len(existing_goals) <= 1:
            for name, target, current in goals:
                if any(g.name == name for g in existing_goals):
                    continue
                db.add(JourneyGoal(
                    client_id=client.id,
                    name=name,
                    target_usd=target,
                    current_usd=current,
                    target_date=date(today.year + 8, 1, 1),
                    monthly_contribution_usd=25000,
                    status="OPEN",
                    product_tags=[],
                ))
        for kind, filename, note in documents:
            db.add(JourneyDocument(client_id=client.id, document_type=kind, file_name=filename, note=note))
        for txn_type, description, amount in transactions:
            db.add(JourneyTransaction(
                client_id=client.id,
                trade_date=today,
                txn_type=txn_type,
                description=description,
                amount_usd=amount,
                currency="USD",
                source="SYNTHETIC_DEMO_DATA",
            ))
        db.add(ClientConversation(
            client_id=client.id,
            conversation_date=today,
            channel="MEETING",
            summary=conversation,
            sentiment="NEUTRAL",
            next_steps="Continue on the journey for this client only.",
        ))
        filled += 1
    if filled:
        await record_event(db, "PLT", "records_completed", detail={"clients": filled})
        await db.commit()
    return filled


def profile_dict(client: DemoClient, investor: JourneyInvestorProfile | None) -> dict:
    expiry = investor.expiry_date if investor else None
    expired = bool(expiry and expiry < date.today())
    return {
        "jurisdiction": jurisdiction_code(client.country),
        "risk_profile": (investor.rpq_band if investor and investor.rpq_band else client.risk_profile) or "Moderate",
        "rpq_band": investor.rpq_band if investor else None,
        "rpq_expired": expired or investor is None,
        "cka_passed": bool(investor and investor.cka_passed),
        "vulnerable": bool(investor and investor.vulnerable),
        "high_risk_segment": bool(investor and investor.high_risk_segment),
        "cross_border_restricted": bool(investor and investor.cross_border_restricted),
        "shariah_compliant": bool(client.shariah_compliant),
        "investor_status": investor.investor_status if investor else "UNKNOWN",
    }


async def _investor(db: AsyncSession, client_id: UUID) -> JourneyInvestorProfile | None:
    return await db.get(JourneyInvestorProfile, client_id)


async def _client(db: AsyncSession, client_id: UUID) -> DemoClient | None:
    return await db.get(DemoClient, client_id)


async def recent_activity(db: AsyncSession, limit: int = 8) -> list[dict]:
    await ensure_seeded(db)
    events = (await db.execute(
        select(JourneyEvent).order_by(JourneyEvent.occurred_at.desc()).limit(limit)
    )).scalars().all()
    clients = {c.id: c for c in (await db.execute(select(DemoClient))).scalars().all()}
    rows = []
    for event in events:
        client = clients.get(event.client_id) if event.client_id else None
        rows.append({
            "stage": event.stage,
            "event": event.event,
            "client_id": str(event.client_id) if event.client_id else None,
            "client_name": _client_name(client) if client else None,
            "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        })
    return rows


async def my_day(db: AsyncSession) -> dict:
    await ensure_seeded(db)
    leads = await ranked_leads(db)
    signals = (await db.execute(select(JourneySignal).where(JourneySignal.active.is_(True)))).scalars().all()
    opps = (await db.execute(select(JourneyOpportunity))).scalars().all()
    notes = (await db.execute(
        select(JourneyNotification).where(JourneyNotification.read.is_(False)).order_by(JourneyNotification.created_at.desc())
    )).scalars().all()
    expiring = [s for s in signals if s.kind == "RPQ_EXPIRY"]
    forecast = sum((o.value_usd or 0) * (o.probability_pct or 0) / 100 for o in opps if o.stage != "SALES_REALIZED")
    return {
        "focus": leads[:10],
        "rpq_expiring": [
            {"client_id": str(s.client_id), "summary": s.summary} for s in expiring
        ],
        "pipeline_open": sum(1 for o in opps if o.stage != "SALES_REALIZED"),
        "weighted_forecast_usd": round(forecast, 2),
        "unread_notifications": len(notes),
        "recent": await recent_activity(db),
        "market_note": "Market news stays on the existing market panel. Signals here are client-specific.",
    }


async def ranked_leads(db: AsyncSession) -> list[dict]:
    await ensure_seeded(db)
    clients = (await db.execute(select(DemoClient))).scalars().all()
    controls = {c.client_id: c.state for c in (await db.execute(select(JourneyLeadControl))).scalars().all()}
    signals = (await db.execute(select(JourneySignal).where(JourneySignal.active.is_(True)))).scalars().all()
    by_client: dict = {}
    for signal in signals:
        by_client.setdefault(signal.client_id, []).append({"kind": signal.kind, "summary": signal.summary})
    rows = []
    for client in clients:
        scored = score_lead(by_client.get(client.id, []), controls.get(client.id))
        if not scored["rankable"]:
            continue
        rows.append({
            "client_id": str(client.id),
            "name": _client_name(client),
            "country": client.country,
            "jurisdiction": jurisdiction_code(client.country),
            "risk_profile": client.risk_profile,
            "aum_usd_millions": client.aum_usd_millions,
            "dnc": False,
            "score": scored["score"],
            "reasons": scored["reasons"],
            "control": controls.get(client.id),
            "next_best_action": scored["reasons"][0] if scored["reasons"] else "Review",
        })
    rows.sort(key=lambda row: (-row["score"], row["name"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


async def set_control(db: AsyncSession, client_id: UUID, state: str) -> None:
    row = await db.get(JourneyLeadControl, client_id)
    if row is None:
        db.add(JourneyLeadControl(client_id=client_id, state=state))
    else:
        row.state = state
        row.updated_at = datetime.now(UTC)
    await record_event(db, "ENGAGE", f"lead_{state.lower()}", client_id)
    await db.commit()


async def search_clients(db: AsyncSession, filters: dict) -> list[dict]:
    leads = await ranked_leads(db)
    q = (filters.get("q") or "").lower()
    out = []
    for row in leads:
        if q and q not in row["name"].lower() and q not in (row["risk_profile"] or "").lower():
            continue
        if filters.get("jurisdiction") and row["jurisdiction"] != filters["jurisdiction"]:
            continue
        if filters.get("risk") and (row["risk_profile"] or "") != filters["risk"]:
            continue
        if filters.get("aum_min") is not None and (row["aum_usd_millions"] or 0) < float(filters["aum_min"]):
            continue
        out.append(row)
    return out


async def client_360(db: AsyncSession, client_id: UUID) -> dict | None:
    await ensure_seeded(db)
    client = await _client(db, client_id)
    if client is None:
        return None
    investor = await _investor(db, client_id)
    financial = await db.get(JourneyFinancialProfile, client_id)
    holdings = (await db.execute(
        select(ClientPortfolioHolding).where(ClientPortfolioHolding.client_id == client_id)
    )).scalars().all()
    goals = (await db.execute(select(JourneyGoal).where(JourneyGoal.client_id == client_id))).scalars().all()
    docs = (await db.execute(select(JourneyDocument).where(JourneyDocument.client_id == client_id))).scalars().all()
    txns = (await db.execute(select(JourneyTransaction).where(JourneyTransaction.client_id == client_id))).scalars().all()
    convos = (await db.execute(
        select(ClientConversation).where(ClientConversation.client_id == client_id).order_by(ClientConversation.conversation_date.desc())
    )).scalars().all()
    opps = (await db.execute(select(JourneyOpportunity).where(JourneyOpportunity.client_id == client_id))).scalars().all()
    allocation: dict[str, float] = {}
    for holding in holdings:
        allocation[holding.asset_class or "Other"] = allocation.get(holding.asset_class or "Other", 0) + float(holding.allocation_pct or 0)
    profile = profile_dict(client, investor)
    profile["aum_usd_millions"] = client.aum_usd_millions
    return {
        "client_id": str(client.id),
        "name": _client_name(client),
        "email": client.email,
        "country": client.country,
        "profile": profile,
        "investor": None if investor is None else {
            "rpq_band": investor.rpq_band,
            "rpq_score": investor.rpq_score,
            "cka_passed": investor.cka_passed,
            "car_status": investor.car_status,
            "investor_status": investor.investor_status,
            "accreditation_evidence": investor.accreditation_evidence,
            "expiry_date": investor.expiry_date.isoformat() if investor.expiry_date else None,
            "vulnerable": investor.vulnerable,
            "high_risk_segment": investor.high_risk_segment,
            "cross_border_restricted": investor.cross_border_restricted,
        },
        "financial_profile": None if financial is None else {
            "annual_income_band": financial.annual_income_band,
            "investable_assets_band": financial.investable_assets_band,
            "liquidity_need": financial.liquidity_need,
            "investment_objective": financial.investment_objective,
            "confirmed_at": financial.confirmed_at.isoformat() if financial.confirmed_at else None,
            "version": financial.version,
            "mandatory_fields": list(FINANCIAL_PROFILE_FIELDS),
        },
        "goals": [
            {
                "id": str(g.id),
                "name": g.name,
                "target_usd": g.target_usd,
                "current_usd": g.current_usd,
                "progress_pct": round(100 * (g.current_usd or 0) / g.target_usd, 1) if g.target_usd else 0,
                "status": g.status,
                "product_tags": g.product_tags or [],
            }
            for g in goals
        ],
        "holdings": [
            {
                "asset_name": h.asset_name,
                "asset_class": h.asset_class,
                "currency": h.currency,
                "value_usd_millions": h.value_usd_millions,
                "allocation_pct": h.allocation_pct,
                "unrealized_gain_pct": h.unrealized_gain_pct,
            }
            for h in holdings
        ],
        "saa": drift_vs_saa(allocation, profile["risk_profile"]),
        "documents": [
            {"id": str(d.id), "type": d.document_type, "file_name": d.file_name, "note": d.note}
            for d in docs
        ],
        "transactions": [
            {
                "date": t.trade_date.isoformat(),
                "type": t.txn_type,
                "description": t.description,
                "amount_usd": t.amount_usd,
                "source": t.source,
            }
            for t in txns
        ],
        "conversations": [
            {
                "date": c.conversation_date.isoformat() if c.conversation_date else None,
                "channel": c.channel,
                "summary": c.summary,
                "next_steps": c.next_steps,
            }
            for c in convos
        ],
        "opportunities": [
            {"id": str(o.id), "title": o.title, "stage": o.stage, "value_usd": o.value_usd, "probability_pct": o.probability_pct}
            for o in opps
        ],
        "label": "SYNTHETIC_DEMO_DATA",
    }


async def save_investor(db: AsyncSession, client_id: UUID, body: dict) -> dict:
    row = await db.get(JourneyInvestorProfile, client_id)
    if row is None:
        row = JourneyInvestorProfile(client_id=client_id)
        db.add(row)
    for field in (
        "rpq_band", "rpq_score", "cka_passed", "car_status", "investor_status",
        "accreditation_evidence", "vulnerable", "high_risk_segment", "cross_border_restricted",
    ):
        if field in body:
            setattr(row, field, body[field])
    if body.get("expiry_date"):
        row.expiry_date = date.fromisoformat(body["expiry_date"])
    if body.get("rpq_answers"):
        row.rpq_answers = body["rpq_answers"]
    row.updated_at = datetime.now(UTC)
    await record_event(db, "DISCOVER", "investor_profile_saved", client_id)
    await db.commit()
    return {"client_id": str(client_id), "expiry_date": row.expiry_date.isoformat() if row.expiry_date else None}


async def save_financial(db: AsyncSession, client_id: UUID, body: dict) -> dict:
    row = await db.get(JourneyFinancialProfile, client_id)
    if row is None:
        row = JourneyFinancialProfile(client_id=client_id, version=1)
        db.add(row)
    missing = [field for field in FINANCIAL_PROFILE_FIELDS if not (body.get(field) or getattr(row, field))]
    for field in FINANCIAL_PROFILE_FIELDS:
        if field in body:
            setattr(row, field, body[field])
    row.version = (row.version or 1) + 1
    await record_event(db, "DISCOVER", "financial_profile_saved", client_id, {"missing": missing})
    await db.commit()
    return {"version": row.version, "missing_mandatory": missing}


async def confirm_unchanged(db: AsyncSession, client_id: UUID, actor: str) -> dict:
    financial = await db.get(JourneyFinancialProfile, client_id)
    investor = await db.get(JourneyInvestorProfile, client_id)
    if financial is None or investor is None:
        return {"ok": False, "reason": "Profile is not on file"}
    missing = [field for field in FINANCIAL_PROFILE_FIELDS if not getattr(financial, field)]
    if missing:
        return {"ok": False, "reason": "Mandatory fields are empty", "missing": missing}
    now = datetime.now(UTC)
    financial.confirmed_at = now
    financial.confirmed_by = actor
    investor.expiry_date = date(date.today().year + 1, date.today().month, min(date.today().day, 28))
    investor.updated_at = now
    await record_event(db, "DISCOVER", "confirm_no_change", client_id, actor=actor)
    await db.commit()
    return {"ok": True, "confirmed_at": now.isoformat(), "expiry_date": investor.expiry_date.isoformat()}


async def add_goal(db: AsyncSession, client_id: UUID, body: dict) -> dict:
    goal = JourneyGoal(
        client_id=client_id,
        name=body["name"],
        target_usd=float(body["target_usd"]),
        target_date=date.fromisoformat(body["target_date"]) if body.get("target_date") else None,
        monthly_contribution_usd=float(body.get("monthly_contribution_usd") or 0),
        current_usd=float(body.get("current_usd") or 0),
        product_tags=body.get("product_tags") or [],
    )
    db.add(goal)
    await record_event(db, "DISCOVER", "goal_created", client_id)
    await db.commit()
    return {"id": str(goal.id), "name": goal.name}


async def assist(db: AsyncSession, client_id: UUID, transcript: str) -> dict:
    from app.services.journey.llm import complete
    import json as _json

    proposals = None
    source = "rules"
    raw = await complete(
        "Extract wealth-profile updates from the RM's notes. Reply with a JSON array only. "
        "Each item is {field, value, evidence}. field is one of risk_profile, investment_objective, goal. "
        "Use only facts written in the notes.",
        transcript or "",
    )
    if raw:
        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = "\n".join(clean.split("\n")[1:]).rsplit("```", 1)[0].strip()
            parsed = _json.loads(clean)
            if isinstance(parsed, list):
                proposals = [
                    item for item in parsed
                    if isinstance(item, dict) and item.get("field") in {"risk_profile", "investment_objective", "goal"}
                ]
                source = "llm"
        except Exception:
            proposals = None
    if not proposals:
        proposals = extract_profile_updates(transcript)
        source = "rules"
    await record_event(db, "DISCOVER", "assist_proposed", client_id, {"count": len(proposals), "source": source})
    await db.commit()
    return {"proposals": proposals, "applied": False, "source": source}


async def accept_assist(db: AsyncSession, client_id: UUID, proposals: list[dict]) -> dict:
    financial = await db.get(JourneyFinancialProfile, client_id)
    investor = await db.get(JourneyInvestorProfile, client_id)
    applied = []
    for item in proposals:
        field = item.get("field")
        value = item.get("value")
        if field == "risk_profile" and investor:
            investor.rpq_band = value
            applied.append(field)
        elif field == "investment_objective" and financial:
            financial.investment_objective = value
            applied.append(field)
        elif field == "goal":
            db.add(JourneyGoal(client_id=client_id, name=value, target_usd=1_000_000, current_usd=0))
            applied.append(field)
    await record_event(db, "DISCOVER", "assist_accepted", client_id, {"applied": applied})
    await db.commit()
    return {"applied": applied}


async def add_document(db: AsyncSession, client_id: UUID, body: dict) -> dict:
    expires = date.fromisoformat(body["expires_on"]) if body.get("expires_on") else None
    doc = JourneyDocument(
        client_id=client_id,
        document_type=body.get("document_type") or "KYC",
        file_name=body["file_name"],
        note=body.get("note"),
        expires_on=expires,
    )
    db.add(doc)
    await db.commit()
    return {"id": str(doc.id), "file_name": doc.file_name}


async def brief_for(db: AsyncSession, client_id: UUID) -> dict | None:
    from app.services.journey.briefing import build_brief

    view = await client_360(db, client_id)
    if view is None:
        return None
    view = {**view, "client_id": str(client_id)}
    return await build_brief(view)


async def copilot(db: AsyncSession, client_id: UUID, question: str, stage: str) -> dict | None:
    """Cross-stage assistant. The reply is grounded in the book and the wealth graph."""
    import json as _json

    from app.services.graph.neo4j_service import client_graph
    from app.services.journey.llm import complete

    view = await client_360(db, client_id)
    if view is None:
        return None
    graph = await client_graph(db, client_id)
    rules = [node["name"] for node in (graph or {}).get("nodes", []) if node.get("kind") == "WealthRule"]
    breaches = [row["bucket"] for row in view.get("saa") or [] if row.get("breach")]
    local = (
        f"{view['name']} is in {stage}. Jurisdiction {(view.get('profile') or {}).get('jurisdiction')}. "
        f"SAA breaches: {', '.join(breaches) or 'none'}. "
        f"Linked rules: {', '.join(rules) or 'none recorded'}. "
        "Suitability and maker-checker rules still apply. This note is not an order."
    )
    rewritten = await complete(
        "Answer the relationship manager using only the context. Do not invent holdings, prices, or approvals.",
        _json.dumps({"question": question, "stage": stage, "context": local, "rules": rules}),
        timeout_s=20,
    )
    return {
        "text": (rewritten or local).strip(),
        "source": "llm" if rewritten else "deterministic",
        "stage": stage,
        "citations": rules,
        "graph_source": (graph or {}).get("source"),
    }


async def shortlist(db: AsyncSession, client_id: UUID, query: str | None = None) -> dict | None:
    client = await _client(db, client_id)
    if client is None:
        return None
    investor = await _investor(db, client_id)
    profile = profile_dict(client, investor)
    q = (query or "").lower()
    rows = []
    for product in CATALOGUE:
        if q and q not in product["name"].lower() and q not in product["saa_bucket"].lower():
            continue
        assessment = assess_product(profile, product)
        rows.append({**product, "assessment": assessment})
    rows.sort(key=lambda row: ({"GREEN": 0, "YELLOW": 1, "RED": 2}[row["assessment"]["rating"]], row["name"]))
    return {"profile": profile, "products": rows, "default_view": "CIO_SHORTLIST"}


async def ask_policy(question: str) -> dict:
    """Policy answer. The model may answer only by citing the local clause library."""
    from app.services.journey.llm import complete

    local = protect_answer(question)
    if not local.get("answered"):
        return {**local, "source": "rules"}
    rewritten = await complete(
        "Answer the RM using only the policy text supplied. Keep the citation ids. "
        "If the text does not cover the question, say insufficient evidence.",
        f"Question: {question}\nPolicy: {local['text']}\nCitations: {', '.join(local['citations'])}",
    )
    if not rewritten:
        return {**local, "source": "rules"}
    return {"answered": True, "text": rewritten.strip(), "citations": local["citations"], "source": "llm"}


async def explain(db: AsyncSession, client_id: UUID, product_id: str) -> dict | None:
    listed = await shortlist(db, client_id)
    if listed is None:
        return None
    product = next((p for p in listed["products"] if p["product_id"] == product_id), None)
    if product is None:
        return None
    drafted = pitch(listed["profile"], product, product["assessment"])
    source = "rules"
    if drafted.get("allowed"):
        from app.services.journey.llm import complete
        rewritten = await complete(
            "Rewrite this product explanation for a client meeting. Use only the facts given. "
            "Do not add returns, fees, or approvals that are not in the text. Two short paragraphs.",
            drafted["text"],
        )
        if rewritten:
            drafted = {**drafted, "text": rewritten.strip()}
            source = "llm"
    return drafted | {"product": product, "assessment": product["assessment"], "source": source}


async def proposal(db: AsyncSession, client_id: UUID) -> dict | None:
    view = await client_360(db, client_id)
    if view is None:
        return None
    allocation = {}
    for row in view["saa"]:
        allocation[row["bucket"]] = row["actual_pct"]
    items = optimise(allocation, view["profile"]["risk_profile"], view["profile"]["shariah_compliant"])
    return {"items": items, "saa": view["saa"], "illustrative": True}


async def pipeline(db: AsyncSession) -> dict:
    await ensure_seeded(db)
    opps = (await db.execute(select(JourneyOpportunity))).scalars().all()
    clients = {c.id: c for c in (await db.execute(select(DemoClient))).scalars().all()}
    rows = []
    for opp in opps:
        client = clients.get(opp.client_id)
        rows.append({
            "id": str(opp.id),
            "client_id": str(opp.client_id),
            "client_name": _client_name(client) if client else "Unknown",
            "title": opp.title,
            "stage": opp.stage,
            "source": opp.source,
            "value_usd": opp.value_usd,
            "probability_pct": opp.probability_pct,
            "weighted_usd": round((opp.value_usd or 0) * (opp.probability_pct or 0) / 100, 2),
        })
    by_stage = {stage: [row for row in rows if row["stage"] == stage] for stage in PIPELINE_STAGES}
    return {
        "stages": PIPELINE_STAGES,
        "board": by_stage,
        "forecast_usd": round(sum(row["weighted_usd"] for row in rows if row["stage"] != "SALES_REALIZED"), 2),
    }


async def advance_opportunity(db: AsyncSession, opp_id: UUID) -> dict | None:
    opp = await db.get(JourneyOpportunity, opp_id)
    if opp is None:
        return None
    nxt = next_stage(opp.stage)
    if nxt:
        opp.stage = nxt
        opp.updated_at = datetime.now(UTC)
    await record_event(db, "ENGAGE", "pipeline_advance", opp.client_id, {"stage": opp.stage})
    await db.commit()
    return {"id": str(opp.id), "stage": opp.stage}


async def outreach(db: AsyncSession, client_ids: list[UUID], message: str) -> dict:
    sent = []
    blocked = []
    for client_id in client_ids:
        client = await _client(db, client_id)
        if client is None:
            blocked.append({"client_id": str(client_id), "reason": "NOT_FOUND"})
            continue
        # DNC is fail-closed when the email is missing.
        if not client.email:
            blocked.append({"client_id": str(client_id), "reason": "NO_CHANNEL"})
            continue
        db.add(JourneyNotification(
            client_id=client_id,
            kind="OUTREACH",
            title=f"Draft to {_client_name(client)}",
            body=message,
            href=f"/journey/discover?client={client_id}",
        ))
        sent.append(str(client_id))
    await record_event(db, "ENGAGE", "outreach_drafted", detail={"sent": len(sent), "blocked": len(blocked)})
    await db.commit()
    return {
        "drafted": sent,
        "blocked": blocked,
        "delivery": "DEMO SINK — not delivered",
        "note": "Each draft still requires RM approval. Nothing was sent.",
    }


async def create_cart(db: AsyncSession, client_id: UUID, items: list[dict], maker: str) -> dict:
    client = await _client(db, client_id)
    if client is None:
        return {"error": "Client not found"}
    investor = await _investor(db, client_id)
    profile = profile_dict(client, investor)
    catalog = {p["product_id"]: p for p in CATALOGUE}
    ratings = []
    cart = JourneyCart(client_id=client_id, maker=maker, status="DRAFT")
    db.add(cart)
    await db.flush()
    stored = []
    for item in items:
        product = catalog.get(item["product_id"])
        if product is None:
            continue
        assessment = assess_product(profile, product)
        ratings.append(assessment["rating"])
        row = JourneyCartItem(
            cart_id=cart.id,
            product_id=product["product_id"],
            order_type=item.get("order_type") or product["order_type"],
            amount_usd=float(item["amount_usd"]),
            side=item.get("side") or "BUY",
            discount_pct=float(item.get("discount_pct") or 0),
            goal_id=UUID(item["goal_id"]) if item.get("goal_id") else None,
        )
        db.add(row)
        stored.append({
            "product_id": product["product_id"],
            "amount_usd": row.amount_usd,
            "complexity": product["complexity"],
            "discount_pct": row.discount_pct,
            "rating": assessment["rating"],
        })
    worst = "RED" if "RED" in ratings else "YELLOW" if "YELLOW" in ratings else "GREEN" if ratings else "YELLOW"
    cart.suitability_rating = worst
    await record_event(db, "ACT", "cart_created", client_id, {"cart_id": str(cart.id)})
    await db.commit()
    return {"cart_id": str(cart.id), "rating": worst, "items": stored}


async def sign_cart(db: AsyncSession, cart_id: UUID, signer: str) -> dict | None:
    cart = await db.get(JourneyCart, cart_id)
    if cart is None:
        return None
    cart.signed_by = signer
    cart.signed_at = datetime.now(UTC)
    cart.status = "SIGNED"
    await record_event(db, "ACT", "client_signed", cart.client_id, {"cart_id": str(cart_id)})
    await db.commit()
    return {"cart_id": str(cart_id), "signed_by": signer, "status": cart.status}


async def submit_cart(db: AsyncSession, cart_id: UUID, maker: str) -> dict | None:
    cart = await db.get(JourneyCart, cart_id)
    if cart is None:
        return None
    client = await _client(db, cart.client_id)
    investor = await _investor(db, cart.client_id)
    profile = profile_dict(client, investor) if client else {}
    items = (await db.execute(select(JourneyCartItem).where(JourneyCartItem.cart_id == cart_id))).scalars().all()
    catalog = {p["product_id"]: p for p in CATALOGUE}
    item_rows = [
        {
            "amount_usd": item.amount_usd,
            "discount_pct": item.discount_pct,
            "complexity": catalog.get(item.product_id, {}).get("complexity"),
        }
        for item in items
    ]
    decision = auto_approval(profile, item_rows, bool(cart.signed_at), cart.suitability_rating or "YELLOW")
    if not cart.signed_at:
        return {"ok": False, "reason": "Client signature is required", "auto": decision}
    approval = JourneyApproval(
        cart_id=cart.id,
        maker=maker,
        status="PENDING",
        reason="; ".join(decision["reasons"]),
    )
    if decision["eligible"]:
        approval.status = "AUTO_APPROVED"
        approval.checker = "policy"
        approval.checker_role = "AUTO"
        approval.decided_at = datetime.now(UTC)
        cart.status = "APPROVED"
        handoff = await _handoff(db, cart, items)
        db.add(approval)
        await db.commit()
        return {"ok": True, "approval": "AUTO_APPROVED", "handoff": handoff, "auto": decision}
    db.add(approval)
    cart.status = "PENDING_APPROVAL"
    await record_event(db, "ACT", "approval_requested", cart.client_id)
    await db.commit()
    return {"ok": True, "approval": "PENDING", "auto": decision, "approval_id": str(approval.id)}


async def _handoff(db: AsyncSession, cart: JourneyCart, items: list[JourneyCartItem]) -> dict:
    payload = {
        "cart_id": str(cart.id),
        "client_id": str(cart.client_id),
        "items": [{"product_id": i.product_id, "amount_usd": i.amount_usd, "side": i.side} for i in items],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    order_id = f"sandbox-{uuid4().hex[:10]}"
    row = JourneyHandoff(
        cart_id=cart.id,
        oms_order_id=order_id,
        status="COMPLETED",
        payload_hash=digest,
        label="DEMO SINK — not submitted",
    )
    db.add(row)
    cart.status = "HANDED_OFF"
    db.add(JourneyNotification(
        client_id=cart.client_id,
        kind="ORDER",
        title="Sandbox order completed",
        body=f"Order {order_id} completed in the OMS sandbox. DEMO SINK — not submitted to a live broker.",
        href="/journey/act",
    ))
    opps = (await db.execute(
        select(JourneyOpportunity).where(JourneyOpportunity.client_id == cart.client_id)
    )).scalars().all()
    for opp in opps:
        if opp.stage != "SALES_REALIZED":
            opp.stage = "SALES_REALIZED"
            break
    await record_event(db, "ACT", "order_handoff", cart.client_id, {"oms_order_id": order_id, "hash": digest})
    return {"oms_order_id": order_id, "status": "COMPLETED", "label": row.label, "payload_hash": digest}


async def decide_approval(db: AsyncSession, approval_id: UUID, actor: str, role: str, decision: str, reason: str) -> dict:
    approval = await db.get(JourneyApproval, approval_id)
    if approval is None:
        return {"ok": False, "reason": "Not found"}
    if actor == approval.maker:
        return {"ok": False, "reason": "Maker cannot be checker"}
    if role not in {"SALES_MANAGER", "COMPLIANCE"}:
        return {"ok": False, "reason": "Role cannot decide"}
    approval.checker = actor
    approval.checker_role = role
    approval.reason = reason
    approval.decided_at = datetime.now(UTC)
    cart = await db.get(JourneyCart, approval.cart_id)
    if decision == "APPROVE":
        approval.status = "APPROVED"
        items = (await db.execute(select(JourneyCartItem).where(JourneyCartItem.cart_id == cart.id))).scalars().all()
        handoff = await _handoff(db, cart, items)
        await db.commit()
        return {"ok": True, "status": "APPROVED", "handoff": handoff}
    approval.status = "REJECTED"
    cart.status = "REJECTED"
    await db.commit()
    return {"ok": True, "status": "REJECTED"}


async def list_approvals(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(select(JourneyApproval))).scalars().all()
    out = []
    for row in rows:
        cart = await db.get(JourneyCart, row.cart_id)
        client = await _client(db, cart.client_id) if cart else None
        investor = await _investor(db, cart.client_id) if cart else None
        queue = "PENDING"
        if investor and investor.vulnerable:
            queue = "VULNERABLE"
        elif investor and investor.high_risk_segment:
            queue = "UNSUITABLE_REVIEW"
        out.append({
            "id": str(row.id),
            "cart_id": str(row.cart_id),
            "client_name": _client_name(client) if client else None,
            "maker": row.maker,
            "status": row.status,
            "reason": row.reason,
            "queue": queue,
            "rating": cart.suitability_rating if cart else None,
        })
    return out


async def list_notifications(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(
        select(JourneyNotification).order_by(JourneyNotification.created_at.desc())
    )).scalars().all()
    return [
        {
            "id": str(row.id),
            "client_id": str(row.client_id) if row.client_id else None,
            "kind": row.kind,
            "title": row.title,
            "body": row.body,
            "href": row.href,
            "read": row.read,
        }
        for row in rows
    ]


async def mark_read(db: AsyncSession, note_id: UUID) -> None:
    row = await db.get(JourneyNotification, note_id)
    if row:
        row.read = True
        await db.commit()


async def evaluate_book(db: AsyncSession) -> dict:
    """Service loop: drift and RPQ expiry become a signal, a task-sized notification, and an opportunity."""
    await ensure_seeded(db)
    clients = (await db.execute(select(DemoClient))).scalars().all()
    raised = 0
    today = date.today()
    for client in clients:
        view = await client_360(db, client.id)
        breaches = [row for row in view["saa"] if row["breach"]] if view["holdings"] else []
        investor = view["investor"]
        expired = investor and investor["expiry_date"] and investor["expiry_date"] < today.isoformat()
        if not breaches and not expired:
            continue
        summary = "SAA drift needs a rebalance conversation" if breaches else "Investor profile needs renewal"
        kind = "SAA_DRIFT" if breaches else "RPQ_EXPIRY"
        already = await db.execute(
            select(JourneySignal.id).where(
                JourneySignal.client_id == client.id,
                JourneySignal.kind == kind,
                JourneySignal.active.is_(True),
                JourneySignal.as_of == today,
            ).limit(1)
        )
        if already.first() is not None:
            continue
        db.add(JourneySignal(client_id=client.id, kind=kind, summary=summary, source="service-evaluator", as_of=today))
        db.add(JourneyOpportunity(
            client_id=client.id,
            title=summary,
            stage="ACTIONABLE",
            source="SERVICE",
            value_usd=100_000,
            probability_pct=25,
        ))
        db.add(JourneyNotification(
            client_id=client.id,
            kind="NUDGE",
            title=summary,
            body="Opened an Actionable opportunity so Engage picks this up on My Day.",
            href=f"/journey?client={client.id}",
        ))
        raised += 1
    await record_event(db, "SERVICE", "evaluator_ran", detail={"raised": raised})
    await db.commit()
    return {"raised": raised}


async def projection(db: AsyncSession, client_id: UUID) -> dict | None:
    view = await client_360(db, client_id)
    if view is None:
        return None
    goals = view["goals"]
    if not goals:
        return {"goals": [], "note": "No saved goals. Discover must record one first."}
    rows = []
    for goal in goals:
        gap = max((goal["target_usd"] or 0) - (goal["current_usd"] or 0), 0)
        rows.append({
            **goal,
            "gap_usd": gap,
            "illustrative": True,
            "disclaimer": "Planning illustration, not advice.",
        })
    return {"goals": rows}


async def run_stress(db: AsyncSession, client_id: UUID, shocks: dict) -> dict | None:
    client = await _client(db, client_id)
    if client is None:
        return None
    total = (client.aum_usd_millions or 0) * 1_000_000
    return stress(total, shocks)


async def save_cohort(db: AsyncSession, name: str, filters: dict) -> dict:
    row = JourneyCohort(name=name, filters=filters)
    db.add(row)
    await db.commit()
    return {"id": str(row.id), "name": name}
