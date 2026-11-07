"""Product comparison service - builds multi-candidate feature matrix.

Architecture §6.7 API-059 - compare selected products across metrics.
Returns feature matrix with consistent metric keys and null for missing data.
"""
from uuid import UUID

from app.schemas.product import Product, ProductRef, ProductComparison, ProductMetric
from app.schemas.common import ArtifactRef


class ComparisonService:
    """Multi-candidate product comparison."""
    
    async def compare_products(
        self,
        tenant_id: str,
        client_id: UUID,
        search_ref: ArtifactRef,
        products: list[Product],
    ) -> ProductComparison:
        """Build comparison matrix across selected products.
        
        Collects union of all metric keys across candidates.
        Missing metrics return null value, not fabricated data.
        Source and as-of preserved per product metric.
        """
        # Collect all unique metric keys across products
        metric_keys: set[str] = set()
        
        for product in products:
            for metric in product.fees:
                metric_keys.add(metric.key)
            for metric in product.liquidity:
                metric_keys.add(metric.key)
            for metric in product.metrics:
                metric_keys.add(metric.key)
            for metric in product.esg:
                metric_keys.add(metric.key)
        
        return ProductComparison(
            search_ref=search_ref,
            products=products,
            metric_keys=sorted(metric_keys),
        )
