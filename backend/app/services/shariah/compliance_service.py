"""
Shariah compliance estimation service for investment products.
Adapted from islamic-ai/shariah contract_analysis.py for WM Workbench.

DEC-05 gated (default OFF).
NOT a fatwa. NOT a religious ruling. Preliminary technical estimate only.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.services.shariah.rag_service import ShariahRagService

logger = logging.getLogger(__name__)

MAX_FINDINGS = 3
MAX_MODEL_TEXT_CHARS = 4000

ANALYSIS_SYSTEM_PROMPT = (
    "You are a Shariah-compliance screening assistant. "
    "Analyse the investment product description against the provided AAOIFI standard excerpts. "
    "Identify potential concerns only — do not issue a Shariah ruling. "
    "Finding categories: Riba (interest/usury), Gharar (excessive uncertainty), "
    "Haram_Sector (prohibited business). Severity: critical, high, medium. "
    "Return at most 3 findings. If no concerns, return empty findings array. "
    "Return exactly this JSON:\n"
    '{"findings": [{"category": "Riba|Gharar|Haram_Sector", "severity": "critical|high|medium", '
    '"description": "short description", "aaoifi_ref": "SS N clause_id or empty string"}]}'
)


def _parse_json(value: str) -> dict[str, Any]:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)
    first, last = cleaned.find("{"), cleaned.rfind("}")
    if first >= 0 and last > first:
        cleaned = cleaned[first : last + 1]
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"findings": []}
    return result if isinstance(result, dict) else {"findings": []}


def _build_source_context(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "No AAOIFI clauses available."
    lines = ["Relevant AAOIFI draft excerpts (not approved/authoritative):"]
    for src in sources:
        lines.append(
            f"- {src['source_key']} | {src['title']} | p.{src['printed_page_start']} | "
            f"{str(src['verbatim_text'])[:600]}"
        )
    return "\n".join(lines)


def _tier_from_findings(findings: list[dict[str, Any]]) -> tuple[str, str, str]:
    """
    Returns (estimate, confidence, tier_label).
    Tier 1: no findings → LIKELY_COMPLIANT
    Tier 2: medium/high only → INSUFFICIENT_DATA (manual review)
    Tier 3: any critical → LIKELY_NON_COMPLIANT
    """
    if not findings:
        return "LIKELY_COMPLIANT", "high", "Tier 1"
    severities = {f.get("severity", "medium") for f in findings}
    if "critical" in severities:
        return "LIKELY_NON_COMPLIANT", "high", "Tier 3"
    return "INSUFFICIENT_DATA", "medium", "Tier 2"


class ShariahComplianceService:
    """
    Evidence-backed Shariah compliance estimation for investment products.
    Uses AAOIFI clause retrieval + LLM analysis.
    DEC-05 gated (default OFF).

    NOT a fatwa. NOT a religious ruling. Preliminary technical estimate only.
    """

    DISCLAIMER = (
        "This is a preliminary technical estimate based on available AAOIFI evidence. "
        "It is NOT a fatwa, religious authority ruling, or compliance approval. "
        "Consult qualified Shariah scholars before making investment decisions."
    )

    def __init__(self) -> None:
        if not settings.database_configured:
            self._rag: ShariahRagService | None = None
        else:
            self._rag = ShariahRagService(db_url=settings.DATABASE_URL)  # type: ignore[arg-type]

    def _check_gate(self) -> None:
        if not settings.SHARIAH_DEC05_ENABLED:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Shariah compliance estimation is not enabled. "
                    "Set SHARIAH_DEC05_ENABLED=true to activate (DEC-05 gate)."
                ),
            )

    async def _call_llm(self, product_description: str, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        source_context = _build_source_context(sources)
        user_prompt = (
            f"{source_context}\n\n"
            f"Investment product description:\n{product_description[:MAX_MODEL_TEXT_CHARS]}"
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": [
                            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "max_tokens": 600,
                        "temperature": 0.1,
                    },
                )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            raw = _parse_json(content)
            findings = raw.get("findings") if isinstance(raw.get("findings"), list) else []
        except Exception as exc:
            # Empty findings would be scored LIKELY_COMPLIANT, so an LLM failure
            # must propagate instead of being mistaken for "no concerns found".
            logger.warning("LLM call failed for compliance estimate: %s", exc)
            raise

        validated: list[dict[str, Any]] = []
        for item in findings[:MAX_FINDINGS]:
            if not isinstance(item, dict):
                continue
            category = item.get("category", "")
            severity = item.get("severity", "")
            if category not in {"Riba", "Gharar", "Haram_Sector"}:
                continue
            if severity not in {"critical", "high", "medium"}:
                severity = "medium"
            validated.append({
                "category": category,
                "severity": severity,
                "description": str(item.get("description", ""))[:400],
                "aaoifi_ref": str(item.get("aaoifi_ref", ""))[:100],
            })
        return validated

    async def estimate_compliance(
        self,
        product_ref: str,
        product_description: str,
        workflow_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Returns:
        {
          "estimate": "LIKELY_COMPLIANT" | "LIKELY_NON_COMPLIANT" | "INSUFFICIENT_DATA",
          "confidence": "high" | "medium" | "low",
          "findings": [...],
          "candidate_sources": [...],
          "disclaimer": str,
          "model_used": str,
        }
        """
        self._check_gate()

        if self._rag is None:
            return {
                "estimate": "INSUFFICIENT_DATA",
                "confidence": "low",
                "findings": [],
                "candidate_sources": [],
                "disclaimer": self.DISCLAIMER,
                "model_used": settings.LLM_MODEL,
                "error": "Database not configured",
            }

        # Retrieve candidate AAOIFI clauses
        try:
            sources = await self._rag.get_candidate_sources(product_description, limit=8)
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            sources = []

        # With no retrieved clauses there is nothing to rely on; an assessment
        # produced from an empty evidence set would be a fabricated conclusion.
        if not sources:
            return {
                "estimate": "INSUFFICIENT_DATA",
                "confidence": "low",
                "findings": [],
                "candidate_sources": [],
                "disclaimer": self.DISCLAIMER,
                "model_used": settings.LLM_MODEL,
                "error": "No AAOIFI clauses matched the supplied description",
            }

        # LLM analysis
        llm_failed = False
        try:
            findings = await self._call_llm(product_description, sources)
        except Exception as exc:
            logger.warning("Compliance LLM analysis failed: %s", exc)
            findings = []
            llm_failed = True

        estimate, confidence, _tier = _tier_from_findings(findings)

        # If LLM failed entirely, downgrade confidence
        if llm_failed:
            estimate = "INSUFFICIENT_DATA"
            confidence = "low"

        return {
            "estimate": estimate,
            "confidence": confidence,
            "findings": findings,
            "candidate_sources": [
                {
                    "source_key": s["source_key"],
                    "title": s["title"],
                    "clause_id": s["clause_id"],
                    "page": s["printed_page_start"],
                    "excerpt": s["verbatim_text"][:400],
                }
                for s in sources
            ],
            "disclaimer": self.DISCLAIMER,
            "model_used": settings.LLM_MODEL,
        }
