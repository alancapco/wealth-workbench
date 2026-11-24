"""AI Assist — meeting summary with grounded profile diffs. Nothing is written until the RM accepts it."""
from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.client_data import DemoClient
from app.models.journey import JourneyEvent, JourneyFinancialProfile, JourneyGoal, JourneyInvestorProfile
from app.services.journey.llm import complete_json
from app.services.journey.logic import extract_profile_updates
from app.services.journey.service import record_event

ALLOWED_FIELDS = {"risk_profile", "investment_objective", "goal"}

SAMPLES = {
    "tan": {
        "title": "Tan Family Office quarterly review",
        "transcript": (
            "RM: Tan Wei Liang, we should confirm the trust and the holding company before the next subscription.\n"
            "Client: The family wants a more balanced income profile. Please treat the risk profile as Balanced.\n"
            "Client: Deploy idle cash into investment-grade SGD bonds. The investment objective is Income.\n"
            "Client: Set a philanthropy goal for the next generation, alongside the education reserve.\n"
            "RM: I will not place anything in the cart until you sign, and a checker reviews anything that is not a straight pass."
        ),
    },
    "ahmad": {
        "title": "Ahmad Rahman Shariah review",
        "transcript": (
            "RM: Ahmad, we will only discuss screened products.\n"
            "Client: Keep the portfolio Shariah compliant. My risk profile stays Moderate.\n"
            "Client: The investment objective is Growth, but only through screened equity and sukuk.\n"
            "Client: Add a goal for the children's education reserve.\n"
            "RM: Non-screened products stay off the shortlist."
        ),
    },
    "default": {
        "title": "Relationship review",
        "transcript": (
            "Client: I want a moderate growth approach and a retirement goal. "
            "Please keep the investment objective as Growth."
        ),
    },
}


def sample_for(name: str) -> dict:
    lowered = (name or "").lower()
    if "tan" in lowered:
        key = "tan"
    elif "ahmad" in lowered or "rahman" in lowered:
        key = "ahmad"
    else:
        key = "default"
    sample = SAMPLES[key]
    return {"persona": key, "title": sample["title"], "transcript": sample["transcript"], "consent_required": True}


def _ground(proposals: list, transcript: str) -> list[dict]:
    haystack = (transcript or "").lower()
    grounded = []
    for item in proposals:
        if not isinstance(item, dict):
            continue
        field = item.get("field")
        value = item.get("value")
        evidence = str(item.get("evidence") or item.get("evidence_quote") or "")
        if field not in ALLOWED_FIELDS or not value or not evidence:
            continue
        if evidence.lower() not in haystack:
            continue
        grounded.append({
            "field": field,
            "value": value,
            "evidence": evidence,
            "before": item.get("before"),
        })
    return grounded


def _fallback_summary(name: str, title: str, transcript: str, proposals: list[dict]) -> dict:
    decisions = [f"Update {item['field']} to {item['value']}" for item in proposals] or [
        "No profile change was explicit in the transcript."
    ]
    return {
        "executive_summary": f"{title} with {name}. The notes below are taken only from the transcript.",
        "key_decisions": decisions,
        "risks_and_concerns": [
            "Profile changes stay as proposals until the RM accepts them.",
            "Orders still require suitability and, where the rules say so, a different checker.",
        ],
        "action_items": [
            "Confirm the accepted profile fields in Discover.",
            "Prepare the shortlist only after the profile is current.",
        ],
        "proposed_profile_updates": proposals,
        "follow_up_email_draft": (
            f"Dear {name},\n\nThank you for the meeting ({title}). "
            "We will update the profile only for the points you confirmed, then return with a suitability-checked shortlist. "
            "Nothing is submitted to the market from this note.\n\nRelationship manager"
        ),
    }


async def summarise(db: AsyncSession, client: DemoClient, title: str, transcript: str, consent: bool) -> dict:
    if not consent:
        return {"ok": False, "reason": "Recording consent is required before a meeting summary is stored."}
    name = f"{client.firstname} {client.lastname}".strip()
    rules = extract_profile_updates(transcript)
    for item in rules:
        item.setdefault("evidence", item.get("evidence") or "")
    drafted = None
    raw = await complete_json(
        "Summarise a wealth-management meeting. Use only the transcript. "
        "Reply with JSON keys executive_summary (string), key_decisions (string list), "
        "risks_and_concerns (string list), action_items (string list), "
        "proposed_profile_updates (list of {field, value, evidence}), follow_up_email_draft (string). "
        "field may only be risk_profile, investment_objective, or goal. "
        "evidence must be a verbatim substring of the transcript.",
        json.dumps({"client": name, "title": title, "transcript": transcript}),
        timeout_s=20,
    )
    source = "deterministic"
    proposals = _ground(rules, transcript)
    if isinstance(raw, dict) and isinstance(raw.get("executive_summary"), str):
        model_proposals = _ground(raw.get("proposed_profile_updates") or [], transcript)
        if model_proposals or not proposals:
            proposals = model_proposals or proposals
        drafted = {
            "executive_summary": raw["executive_summary"].strip(),
            "key_decisions": [str(x) for x in raw.get("key_decisions") or []],
            "risks_and_concerns": [str(x) for x in raw.get("risks_and_concerns") or []],
            "action_items": [str(x) for x in raw.get("action_items") or []],
            "proposed_profile_updates": proposals,
            "follow_up_email_draft": str(raw.get("follow_up_email_draft") or ""),
        }
        source = "llm"
    if drafted is None:
        drafted = _fallback_summary(name, title, transcript, proposals)
    event = await record_event(
        db,
        "DISCOVER",
        "meeting_summary",
        client.id,
        {
            "title": title,
            "transcript": transcript,
            "source": source,
            "model": settings.LLM_MODEL if source == "llm" else None,
            **drafted,
            "applied": False,
        },
    )
    await db.commit()
    await db.refresh(event)
    return {"ok": True, "meeting_id": str(event.id), "source": source, "model": settings.LLM_MODEL if source == "llm" else None, **drafted}


async def apply_updates(db: AsyncSession, client_id: UUID, meeting_id: UUID, accepted: list[dict]) -> dict:
    event = await db.get(JourneyEvent, meeting_id)
    if event is None or event.event != "meeting_summary" or event.client_id != client_id:
        return {"ok": False, "reason": "Meeting summary not found"}
    detail = dict(event.detail or {})
    allowed = {(item.get("field"), str(item.get("value"))) for item in detail.get("proposed_profile_updates") or []}
    investor = await db.get(JourneyInvestorProfile, client_id)
    financial = await db.get(JourneyFinancialProfile, client_id)
    applied = []
    for item in accepted:
        field = item.get("field")
        value = str(item.get("value") or "")
        if (field, value) not in allowed:
            continue
        if field == "risk_profile" and investor is not None:
            investor.rpq_band = value
            applied.append({"field": field, "value": value})
        elif field == "investment_objective" and financial is not None:
            financial.investment_objective = value
            applied.append({"field": field, "value": value})
        elif field == "goal" and value:
            db.add(JourneyGoal(client_id=client_id, name=value, target_usd=1_000_000, current_usd=0))
            applied.append({"field": field, "value": value})
    detail["applied"] = True
    detail["applied_fields"] = applied
    event.detail = detail
    await record_event(db, "DISCOVER", "meeting_updates_applied", client_id, {"meeting_id": str(meeting_id), "applied": applied})
    await db.commit()
    return {"ok": True, "applied": applied}
