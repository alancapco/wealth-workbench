"""Product catalog search adapter - UNCONFIGURED stub without provider integration.

Architecture §6.7 API-058 - search current entitled synthetic products.
No live product provider calls authorized; returns UNCONFIGURED without DEC-04 catalog.
"""
from typing import Any
from uuid import UUID

from app.schemas.product import Product, ProductFilter, ProductRef
from app.schemas.common import Availability, CapabilityState, Environment, EnvironmentKind, Source, Origin


class ProductSearchService:
    """Product catalog search - UNCONFIGURED without approved provider."""
    
    def __init__(self, environment: Environment):
        self.environment = environment
    
    async def search_products(
        self,
        tenant_id: str,
        client_id: UUID,
        filters: list[ProductFilter],
        universe_ref_id: UUID,
    ) -> tuple[list[Product], str | None, CapabilityState]:
        """Search entitled products matching confirmed filters.
        
        Returns:
            - products: matching product list (empty if UNCONFIGURED)
            - next_cursor: pagination cursor or None
            - capability_state: UNCONFIGURED without DEC-04 provider
        
        No live product provider calls. Returns empty results with UNCONFIGURED state.
        Real implementation requires approved DEC-04 catalog configuration.
        """
        # UNCONFIGURED: no approved product catalog provider configured
        # Real implementation would:
        # 1. Resolve universe_ref to entitled product catalog
        # 2. Apply hard filters (immutable restrictions)
        # 3. Apply confirmed soft filters (RM-edited preferences)
        # 4. Query entitled product provider with tenant/client scope
        # 5. Return actual products with real source evidence
        
        return [], None, CapabilityState.UNCONFIGURED
    
    async def get_product_details(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
    ) -> Product | None:
        """Retrieve single product details by reference.
        
        Returns None if product not found or not entitled.
        UNCONFIGURED without approved product provider.
        """
        # UNCONFIGURED: no product provider
        return None
