"""AI Prepare — five-section meeting brief. Numbers stay in the supplied facts."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from app.core.config import settings
from app.services.journey.llm import complete_json

SECTIONS = (
    "portfolio_overview",
    "material_changes",
    "recent_interactions",
    "market_news",
    "proposed_agenda",
)


def _section(narrative: str, origin: str) -> dict:
    return {
        "narrative": narrative,
        "content": narrative,
        "availability": "AVAILABLE",
        "capability_state": "AVAILABLE",
        "completeness": "COMPLETE",
        "claims": [{"id": "c1", "text": narrative, "origin": origin, "evidence_refs": []}],
        "sources": [{
            "id": origin,
            "environment": {"kind": "FIXTURE", "id": "demo"},
            "availability": "AVAILABLE",
            "origin": origin,
            "live_response": origin == "llm",
            "as_of": datetime.now(UTC).date().isoformat(),
            "retrieved_at": datetime.now(UTC).isoformat(),
            "limitation_codes": ["SYNTHETIC_DEMO_DATA"],
        }],
        "limitations": [],
        "agenda": [],
        "content_hash": hashlib.sha256(narrative.encode()).hexdigest(),
    }


def _facts(view: dict) -> dict:
    holdings = view.get("holdings") or []
    saa = view.get("saa") or []
    breaches = [row for row in saa if row.get("breach")]
    top = sorted(holdings, key=lambda row: row.get("allocation_pct") or 0, reverse=True)[:3]
    return {
        "name": view.get("name"),
        "jurisdiction": (view.get("profile") or {}).get("jurisdiction"),
        "shariah": (view.get("profile") or {}).get("shariah_compliant"),
        "aum_usd_millions": (view.get("profile") or {}).get("aum_usd_millions"),
        "rpq": (view.get("investor") or {}).get("rpq_band"),
        "rpq_expiry": (view.get("investor") or {}).get("expiry_date"),
        "vulnerable": (view.get("investor") or {}).get("vulnerable"),
        "objective": (view.get("financial_profile") or {}).get("investment_objective"),
        "holding_count": len(holdings),
        "largest_holdings": [
            {"name": row.get("asset_name"), "allocation_pct": row.get("allocation_pct")}
            for row in top
        ],
        "saa_breaches": [
            {"bucket": row.get("bucket"), "actual_pct": row.get("actual_pct"), "target_pct": row.get("target_pct")}
            for row in breaches
        ],
        "opportunities": [row.get("stage") for row in (view.get("opportunities") or [])],
    }


def _fallback(facts: dict) -> dict[str, str]:
    largest = facts["largest_holdings"]
    largest_text = ", ".join(
        f"{row['name']} {row['allocation_pct']}%" for row in largest if row.get("name")
    ) or "no positions on file"
    breaches = facts["saa_breaches"]
    breach_text = (
        "; ".join(f"{row['bucket']} {row['actual_pct']}% vs target {row['target_pct']}%" for row in breaches)
        if breaches
        else "no SAA bucket is in breach"
    )
    shariah = (
        "Shariah preference is on. Keep the shortlist inside AAOIFI-screened products."
        if facts["shariah"]
        else "No Shariah constraint is recorded."
    )
    vulnerable = " Vulnerable-client handling applies; auto-approval must not fire." if facts["vulnerable"] else ""
    return {
        "portfolio_overview": (
            f"{facts['name']} ({facts['jurisdiction']}) has {facts['holding_count']} positions. "
            f"Largest: {largest_text}. AUM USD {facts['aum_usd_millions']}M."
        ),
        "material_changes": (
            f"RPQ {facts['rpq'] or 'not recorded'} expires {facts['rpq_expiry'] or 'unknown'}. "
            f"Objective: {facts['objective'] or 'not confirmed'}. SAA: {breach_text}."
        ),
        "recent_interactions": (
            f"Open pipeline stages: {', '.join(facts['opportunities']) or 'none'}."
        ),
        "market_news": f"{shariah}{vulnerable} Use the market panel for headlines on names in this book.",
        "proposed_agenda": (
            "1. Confirm the investor and financial profile. 2. Review SAA drift. "
            "3. Walk only GREEN or checker-approved products. 4. Cart after the client signs."
        ),
    }


async def build_brief(view: dict) -> dict:
    facts = _facts(view)
    drafted = _fallback(facts)
    source = "deterministic"
    model = None
    raw = await complete_json(
        "You write a private-banker pre-meeting brief. Use only the JSON facts. "
        "Do not invent holdings, returns, or regulatory citations. "
        "Reply with JSON object keys portfolio_overview, material_changes, recent_interactions, "
        "market_news, proposed_agenda. Each value is a short paragraph.",
        json.dumps(facts),
        timeout_s=20,
    )
    if isinstance(raw, dict) and all(isinstance(raw.get(key), str) and raw.get(key).strip() for key in SECTIONS):
        drafted = {key: raw[key].strip() for key in SECTIONS}
        source = "llm"
        model = settings.LLM_MODEL
    return {
        "brief_id": str(view.get("client_id") or ""),
        "client_id": str(view.get("client_id") or ""),
        "client_name": facts["name"],
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "generated_by": "ai-prepare",
        "environment": {"kind": "FIXTURE", "id": "demo"},
        "blockers": [],
        "ai": {"source": source, "model": model, "grounded_in": "client book, holdings, SAA drift"},
        "sections": {key: _section(drafted[key], source) for key in SECTIONS},
    }
