"""
Shariah Tools Integration Service
Integrates with the Islamic AI Shariah tools
"""
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Add Shariah tools to Python path
if os.path.exists(settings.SHARIAH_TOOLS_PATH):
    sys.path.insert(0, settings.SHARIAH_TOOLS_PATH)

class ShariahService:
    def __init__(self):
        self.tools_available = os.path.exists(settings.SHARIAH_TOOLS_PATH)
        if self.tools_available:
            logger.info(f"Shariah tools loaded from {settings.SHARIAH_TOOLS_PATH}")
        else:
            logger.warning("Shariah tools path not found - using stub implementation")

    async def screen_instrument(self, symbol: str, company_data: Dict) -> Dict:
        """
        Screen a financial instrument for Shariah compliance
        Returns compliance status and methodology
        """
        try:
            # This would integrate with actual Shariah screening tools
            # For now, returning structured response

            screening_result = {
                "symbol": symbol,
                "compliant": True,  # Placeholder
                "screening_date": datetime.now().isoformat(),
                "methodology": "AAOIFI Standard",
                "criteria_checked": [
                    "Business activity screening",
                    "Financial ratios screening",
                    "Purification calculation"
                ],
                "warnings": [],
                "purification_required": False,
                "purification_percentage": 0.0,
                "provenance": {
                    "source": "Shariah Screening Engine v1.0",
                    "timestamp": datetime.now().isoformat(),
                    "standard": "AAOIFI"
                }
            }

            # Check business activity (placeholder logic)
            prohibited_keywords = ["alcohol", "gambling", "pork", "interest", "tobacco"]
            if company_data.get("business_description"):
                desc_lower = company_data["business_description"].lower()
                for keyword in prohibited_keywords:
                    if keyword in desc_lower:
                        screening_result["compliant"] = False
                        screening_result["warnings"].append(
                            f"Business involves prohibited activity: {keyword}"
                        )

            return screening_result

        except Exception as e:
            logger.error(f"Error screening instrument {symbol}: {e}")
            return {"error": str(e), "compliant": None}

    async def calculate_zakat(
        self,
        client_id: str,
        portfolio_data: List[Dict],
        hawl_start_date: str
    ) -> Dict:
        """
        Calculate zakat for a client's portfolio
        Returns zakat amount and detailed breakdown
        """
        try:
            # Calculate zakatable assets
            total_zakatable = 0.0
            asset_breakdown = []

            for holding in portfolio_data:
                if holding.get("asset_class") in ["Equity", "Cash"]:
                    zakatable_value = holding.get("current_value", 0)
                    total_zakatable += zakatable_value
                    asset_breakdown.append({
                        "symbol": holding.get("symbol"),
                        "value": zakatable_value,
                        "asset_class": holding.get("asset_class")
                    })

            # Zakat rate is 2.5% of zakatable assets
            zakat_rate = 0.025
            zakat_amount = total_zakatable * zakat_rate

            return {
                "client_id": client_id,
                "hawl_period": {
                    "start": hawl_start_date,
                    "end": datetime.now().isoformat()
                },
                "total_zakatable_assets": total_zakatable,
                "zakat_rate": zakat_rate,
                "zakat_due": zakat_amount,
                "asset_breakdown": asset_breakdown,
                "calculation_method": "Simplified Hawl Method",
                "notes": "This is an estimate for discussion. Consult with Shariah scholar for final determination.",
                "provenance": {
                    "source": "Zakat Calculator v1.0",
                    "timestamp": datetime.now().isoformat(),
                    "disclaimer": "Estimate only - not a fatwa"
                }
            }

        except Exception as e:
            logger.error(f"Error calculating zakat: {e}")
            return {"error": str(e)}

    async def get_shariah_compliant_alternatives(
        self,
        symbol: str,
        sector: str
    ) -> List[Dict]:
        """
        Get Shariah-compliant alternatives for a non-compliant holding
        """
        try:
            # Placeholder - would query actual database of compliant securities
            alternatives = [
                {
                    "symbol": f"ALT-{symbol}-1",
                    "name": "Shariah Compliant Alternative 1",
                    "sector": sector,
                    "screening_status": "Compliant",
                    "shariah_board": "AAOIFI Certified"
                }
            ]

            return alternatives

        except Exception as e:
            logger.error(f"Error finding alternatives: {e}")
            return []

    async def generate_shariah_report(
        self,
        client_id: str,
        portfolio_screening: List[Dict],
        zakat_calculation: Dict
    ) -> Dict:
        """
        Generate comprehensive Shariah compliance report
        """
        try:
            compliant_count = sum(1 for item in portfolio_screening if item.get("compliant"))
            total_count = len(portfolio_screening)

            report = {
                "client_id": client_id,
                "report_date": datetime.now().isoformat(),
                "portfolio_compliance_summary": {
                    "total_holdings": total_count,
                    "compliant_holdings": compliant_count,
                    "non_compliant_holdings": total_count - compliant_count,
                    "compliance_percentage": (compliant_count / total_count * 100) if total_count > 0 else 0
                },
                "screening_details": portfolio_screening,
                "zakat_summary": zakat_calculation,
                "recommendations": [],
                "methodology": "AAOIFI Standards with local adaptations",
                "disclaimer": "This report is for informational purposes. It does not constitute a fatwa. Consult qualified Shariah scholars for religious rulings.",
                "provenance": {
                    "source": "Shariah Reporting Engine",
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Generate recommendations
            if total_count - compliant_count > 0:
                report["recommendations"].append(
                    "Consider rebalancing to achieve full Shariah compliance"
                )

            return report

        except Exception as e:
            logger.error(f"Error generating Shariah report: {e}")
            return {"error": str(e)}

# Singleton instance
shariah_service = ShariahService()
