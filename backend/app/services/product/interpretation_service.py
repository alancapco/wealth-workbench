"""Product query interpretation service - extracts structured criteria from natural language.

Architecture §6.7 API-056 - interpret query to editable filters.
Extracts objective, timeframe, amount, risk, and other criteria from natural text.
"""
from typing import Any
from uuid import UUID, uuid4

from app.schemas.product import ProductFilter, ProductInterpretation, FilterOperator
from app.schemas.common import CatalogRef, ConfigRef, FieldValue, FieldValueType


class InterpretationService:
    """Natural language query interpreter - extracts product search criteria."""
    
    def __init__(self, universe_config_ref: ConfigRef, catalog_ref: CatalogRef):
        self.universe_config_ref = universe_config_ref
        self.catalog_ref = catalog_ref
    
    async def interpret_query(
        self,
        tenant_id: str,
        client_id: UUID,
        query: str,
    ) -> ProductInterpretation:
        """Extract structured filters from natural language query.
        
        Real implementation would:
        1. Parse query for investment objective terms
        2. Extract timeframe indicators (short/medium/long-term)
        3. Identify amount/currency mentions
        4. Extract risk tolerance keywords
        5. Identify asset class preferences
        6. Flag ambiguities requiring RM confirmation
        
        Returns editable confirmed filters. Ambiguities block search until resolved.
        Hard filters (regulatory/policy restrictions) are immutable.
        """
        # Stub: extract basic criteria
        filters: list[ProductFilter] = []
        ambiguities: list[str] = []
        
        # Simple keyword extraction (real implementation uses approved NLP)
        query_lower = query.lower()
        
        # Example: detect risk mentions
        if "low risk" in query_lower or "conservative" in query_lower:
            filters.append(ProductFilter(
                key="risk_level",
                operator="EQ",
                value=FieldValue(type=FieldValueType.CHOICE, value="LOW"),
                metric_key=None,
                unit=None,
                source="QUERY",
                hard=False,
                confirmed=False,  # Requires RM confirmation
                catalog_ref=self.catalog_ref,
            ))
        elif "high risk" in query_lower or "aggressive" in query_lower:
            filters.append(ProductFilter(
                key="risk_level",
                operator="EQ",
                value=FieldValue(type=FieldValueType.CHOICE, value="HIGH"),
                metric_key=None,
                unit=None,
                source="QUERY",
                hard=False,
                confirmed=False,
                catalog_ref=self.catalog_ref,
            ))
        
        # Flag ambiguity if timeframe unclear
        if "term" not in query_lower and "year" not in query_lower:
            ambiguities.append("Investment timeframe not specified - please confirm horizon")
        
        return ProductInterpretation(
            query=query,
            filters=filters,
            sort_key=None,
            universe_ref=self.universe_config_ref,
            profile_ref=None,
            ambiguities=ambiguities,
        )
