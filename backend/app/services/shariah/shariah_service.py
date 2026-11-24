"""Shariah screening service.

Preliminary technical assessment only — NOT a religious ruling (PRD §5.7).
Clause retrieval and assessment are delegated to the in-repo AAOIFI RAG /
compliance services (rag_service.py, compliance_service.py, models/aaoifi.py).
No external "Shariah Tools" package, no fabricated provenance, no verdict
without approved clauses to rely on.
"""
from datetime import datetime, UTC
from typing import Dict, List

from app.core.config import settings
from app.services.shariah.compliance_service import ShariahComplianceService

# Reuse the single approved disclaimer so every result states the same limitation.
DISCLAIMER = ShariahComplianceService.DISCLAIMER

ASSESSMENT_MAP = {
    "LIKELY_COMPLIANT": "LIKELY_COMPLIANT",
    "LIKELY_NON_COMPLIANT": "LIKELY_NON_COMPLIANT",
    "INSUFFICIENT_DATA": "INSUFFICIENT_INFORMATION",
}
CRITERIA = [
    "Riba (prohibited returns)",
    "Gharar (excessive uncertainty)",
    "Haram_Sector (prohibited business)",
]


class ShariahService:
    def __init__(self):
        self._compliance = ShariahComplianceService()

    @staticmethod
    def _instrument_description(symbol: str, company_data: Dict) -> str:
        """Build a RAG query from real instrument fields only; never infer facts."""
        fields = (
            "symbol", "name", "business_description", "sector", "asset_class",
            "quantity", "cost_basis", "current_value", "currency", "source_kind", "as_of",
        )
        parts = [
            f"{key}={company_data[key]}"
            for key in fields
            if company_data.get(key) not in (None, "")
        ]
        return "; ".join(parts) or symbol

    def _result_base(self, symbol: str) -> Dict:
        """Common honest result: no compliance verdict until evidence is available."""
        return {
            "symbol": symbol,
            "compliant": None,
            "assessment": "INSUFFICIENT_INFORMATION",
            "confidence": "low",
            "screening_date": datetime.now(UTC).isoformat(),
            "methodology": "AAOIFI clause retrieval + preliminary technical assessment",
            "criteria_checked": list(CRITERIA),
            "warnings": [],
            "purification_required": None,
            "purification_percentage": None,
            "clauses_relied_on": [],
            "findings": [],
            "disclaimer": DISCLAIMER,
            "is_religious_ruling": False,
            "provenance": {
                "source": "app.services.shariah.rag_service / compliance_service (AAOIFI clauses)",
                "standard": "AAOIFI",
                "timestamp": datetime.now(UTC).isoformat(),
                "approved_clause_count": 0,
                "board_approval": "OUTSTANDING",
            },
        }

    async def screen_instrument(self, symbol: str, company_data: Dict) -> Dict:
        """Screen an instrument against retrieved AAOIFI clauses (not a ruling)."""
        result = self._result_base(symbol)
        description = self._instrument_description(symbol, company_data)

        if not settings.SHARIAH_DEC05_ENABLED:
            result["warnings"].append(
                "Screening pilot is disabled (DEC-05 gate off); no assessment was made."
            )
            return result

        try:
            estimate = await self._compliance.estimate_compliance(
                product_ref=symbol, product_description=description
            )
        except Exception as exc:
            # A failed retrieval/analysis is not evidence of compliance.
            result["warnings"].append(f"Screening unavailable: {exc}")
            return result

        clauses = estimate.get("candidate_sources") or []
        findings = estimate.get("findings") or []
        assessment = ASSESSMENT_MAP.get(
            estimate.get("estimate", "INSUFFICIENT_DATA"), "INSUFFICIENT_INFORMATION"
        )

        result["clauses_relied_on"] = clauses
        result["findings"] = findings
        result["provenance"]["approved_clause_count"] = len(clauses)
        result["confidence"] = estimate.get("confidence", "low")
        result["warnings"] = [
            f"{f.get('category')} ({f.get('severity')}): {f.get('description')}"
            for f in findings
        ]

        if not clauses or assessment == "INSUFFICIENT_INFORMATION":
            result["warnings"].append(
                "No matching AAOIFI clauses or no verified analysis available; "
                "insufficient information for an assessment."
            )
            if estimate.get("error"):
                result["warnings"].append(estimate["error"])
            return result

        result["assessment"] = assessment
        result["compliant"] = assessment == "LIKELY_COMPLIANT"
        result["purification_required"] = False
        result["purification_percentage"] = None
        return result

    async def calculate_zakat(
        self,
        client_id: str,
        portfolio_data: List[Dict],
        hawl_start_date: str | None,
    ) -> Dict:
        """Simplified zakat estimate over recorded holdings — NOT a ruling."""
        total_zakatable = 0.0
        asset_breakdown = []

        for holding in portfolio_data:
            if holding.get("asset_class") in ["Equity", "Cash"]:
                zakatable_value = holding.get("current_value", 0) or 0
                total_zakatable += zakatable_value
                asset_breakdown.append({
                    "symbol": holding.get("symbol"),
                    "value": zakatable_value,
                    "asset_class": holding.get("asset_class"),
                })

        zakat_rate = 0.025
        return {
            "client_id": client_id,
            "hawl_period": {
                "start": hawl_start_date,
                "end": datetime.now(UTC).isoformat(),
                "verified": hawl_start_date is not None,
            },
            "total_zakatable_assets": total_zakatable,
            "zakat_rate": zakat_rate,
            "zakat_due": total_zakatable * zakat_rate,
            "asset_breakdown": asset_breakdown,
            "calculation_method": "Simplified 2.5% estimate over recorded Equity/Cash values",
            "notes": (
                "Nisab, lunar hawl and purification are not verified. This is a "
                "planning estimate, not a religious determination."
            ),
            "disclaimer": DISCLAIMER,
            "is_religious_ruling": False,
            "provenance": {
                "source": "Recorded holding values (no certified zakat rule pack)",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }

    async def get_shariah_compliant_alternatives(
        self,
        symbol: str,
        sector: str,
    ) -> List[Dict]:
        """No approved alternatives registry exists; never invent certified products."""
        return [{
            "symbol": symbol,
            "sector": sector,
            "status": "INSUFFICIENT_INFORMATION",
            "reason": "No approved registry of Shariah-compliant alternatives is available.",
            "disclaimer": DISCLAIMER,
            "is_religious_ruling": False,
        }]

    async def generate_shariah_report(
        self,
        client_id: str,
        portfolio_screening: List[Dict],
        zakat_calculation: Dict,
    ) -> Dict:
        """Aggregate per-instrument assessments — every count is evidence-based."""
        total_count = len(portfolio_screening)
        assessments = [
            item.get("assessment", "INSUFFICIENT_INFORMATION")
            for item in portfolio_screening
        ]
        compliant_count = sum(a == "LIKELY_COMPLIANT" for a in assessments)
        non_compliant_count = sum(a == "LIKELY_NON_COMPLIANT" for a in assessments)
        insufficient_count = sum(a == "INSUFFICIENT_INFORMATION" for a in assessments)

        recommendations = []
        if non_compliant_count:
            recommendations.append(
                "Holdings flagged likely-non-compliant require review by a qualified "
                "Shariah scholar before any action."
            )
        if insufficient_count:
            recommendations.append(
                f"Insufficient matching AAOIFI evidence for {insufficient_count} "
                "holding(s); no assessment was made — review the holdings before concluding."
            )
        if not recommendations:
            recommendations.append(
                "Discuss the preliminary assessment with a qualified Shariah scholar."
            )

        return {
            "client_id": client_id,
            "report_date": datetime.now(UTC).isoformat(),
            "portfolio_compliance_summary": {
                "total_holdings": total_count,
                "compliant_holdings": compliant_count,
                "non_compliant_holdings": non_compliant_count,
                "insufficient_information_holdings": insufficient_count,
                "compliance_percentage": (
                    round(compliant_count / total_count * 100, 2) if total_count else 0
                ),
            },
            "screening_details": portfolio_screening,
            "zakat_summary": zakat_calculation,
            "recommendations": recommendations,
            "methodology": "Preliminary technical assessment against retrieved AAOIFI clauses",
            "disclaimer": DISCLAIMER,
            "is_religious_ruling": False,
            "provenance": {
                "source": "In-repo AAOIFI clause retrieval + recorded portfolio holdings",
                "timestamp": datetime.now(UTC).isoformat(),
                "board_approval": "OUTSTANDING",
            },
        }


# Singleton instance
shariah_service = ShariahService()
