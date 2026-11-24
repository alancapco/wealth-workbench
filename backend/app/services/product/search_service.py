"""Product catalog search backed by the approved, entitled product universe.

Architecture §6.7 API-058. The universe is an APPROVED CATALOG configuration
revision: its id/revision/content_hash are the real provenance of every returned
product, and its scope decides which tenant/market the catalog is entitled to.
"""
from datetime import datetime, UTC
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import ConfigurationRevision
from app.schemas.product import Product, ProductFilter, ProductMetric, ProductRef
from app.schemas.common import (
    Availability,
    CapabilityState,
    ConfigRef,
    Environment,
    FieldValue,
    FieldValueType,
    Money,
    Origin,
    Source,
)
from app.services.product.config_refs import (
    UNIVERSE_CONFIG_CLASS,
    UNIVERSE_CONFIG_KEY,
    parse_config_value,
    resolve_approved_config,
    to_config_ref,
)


def _eq(actual: Any, expected: Any) -> bool:
    left, right = str(actual), str(expected)
    try:
        return Decimal(left) == Decimal(right)
    except (InvalidOperation, ValueError):
        return left.strip().upper() == right.strip().upper()


def _num(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _filter_field(record: dict, flt: ProductFilter) -> Any:
    aliases = {"risk_level": "risk_code", "currency": "currencies", "currencies": "currencies"}
    value = record.get(flt.key)
    if value is None and flt.key in aliases:
        value = record.get(aliases[flt.key])
    if value is not None:
        return value
    for group in ("fees", "liquidity", "metrics", "esg"):
        for metric in record.get(group) or []:
            if isinstance(metric, dict) and metric.get("key") in (flt.metric_key, flt.key):
                raw = metric.get("value")
                return raw.get("value") if isinstance(raw, dict) else raw
    return None


def _matches(record: dict, flt: ProductFilter) -> bool:
    actual = _filter_field(record, flt)
    expected = flt.value.value
    if actual is None or expected is None:
        return False
    actual_values = actual if isinstance(actual, list) else [actual]
    if flt.operator == "IN":
        expected_values = expected if isinstance(expected, list) else [expected]
        return any(_eq(a, e) for a in actual_values for e in expected_values)
    if flt.operator == "EQ":
        return any(_eq(a, expected) for a in actual_values)
    left, right = _num(actual_values[0]), _num(expected)
    if left is None or right is None:
        return False
    return left >= right if flt.operator == "GTE" else left <= right


class ProductSearchService:
    """Search the current approved universe for entitled products."""

    def __init__(self, environment: Environment, db: AsyncSession | None = None):
        self.environment = environment
        self.db = db
        self.capability_reason: str | None = None

    async def _approved_universe(
        self, tenant_id: str, jurisdiction: str | None
    ) -> ConfigurationRevision | None:
        if self.db is None:
            self.capability_reason = "No database session supplied for the product catalog."
            return None
        row, self.capability_reason = await resolve_approved_config(
            self.db, tenant_id, UNIVERSE_CONFIG_CLASS, UNIVERSE_CONFIG_KEY, jurisdiction
        )
        return row

    @staticmethod
    def _records(row: ConfigurationRevision) -> list[dict]:
        products = parse_config_value(row).get("products")
        return [p for p in products if isinstance(p, dict)] if isinstance(products, list) else []

    @staticmethod
    def _entitled(record: dict, tenant_id: str, client_id: UUID) -> bool:
        tenants = record.get("entitled_tenants")
        clients = record.get("entitled_clients")
        if tenants is not None and tenant_id not in [str(t) for t in tenants]:
            return False
        if clients is not None and str(client_id) not in [str(c) for c in clients]:
            return False
        return True

    def _source(self, row: ConfigurationRevision) -> Source:
        return Source(
            id=row.id,
            environment=self.environment,
            availability=Availability.AVAILABLE,
            origin=Origin.RECORDED,
            system_key="CONFIG_CATALOG",
            record_id=str(row.id),
            record_version=str(row.revision),
            as_of=row.created_at,
            retrieved_at=datetime.now(UTC),
            authoritative_owner="product_governance",
            live_response=False,
            limitation_codes=[],
        )

    @staticmethod
    def _metric(item: Any, definition_ref: ConfigRef, source: Source) -> ProductMetric | None:
        if not isinstance(item, dict) or not item.get("key"):
            return None
        raw = item.get("value")
        value = None
        if isinstance(raw, dict) and raw.get("type") and "value" in raw:
            try:
                value = FieldValue(type=FieldValueType(raw["type"]), value=raw["value"])
            except ValueError:
                value = None
        return ProductMetric(
            key=item["key"],
            name=item.get("name") or item["key"],
            value=value,
            unit=item.get("unit"),
            definition_ref=definition_ref,
            source=source,
        )

    def _to_product(
        self, record: dict, definition_ref: ConfigRef, source: Source
    ) -> Product | None:
        ref = record.get("ref")
        if not isinstance(ref, dict) or not ref.get("id") or not ref.get("version"):
            return None
        if not record.get("name") or not record.get("asset_class"):
            return None

        minimum = None
        raw_minimum = record.get("minimum_investment")
        if isinstance(raw_minimum, dict) and raw_minimum.get("amount") is not None:
            try:
                minimum = Money(
                    amount=Decimal(str(raw_minimum["amount"])),
                    currency=str(raw_minimum.get("currency", "USD")),
                )
            except (InvalidOperation, ValueError):
                minimum = None

        def metrics(group: str) -> list[ProductMetric]:
            built = [
                self._metric(item, definition_ref, source)
                for item in record.get(group) or []
            ]
            return [m for m in built if m is not None]

        return Product(
            ref=ProductRef(id=str(ref["id"]), version=str(ref["version"])),
            name=record["name"],
            asset_class=record["asset_class"],
            currencies=[str(c) for c in record.get("currencies") or []],
            risk_code=record.get("risk_code"),
            minimum_investment=minimum,
            fees=metrics("fees"),
            liquidity=metrics("liquidity"),
            metrics=metrics("metrics"),
            esg=metrics("esg"),
            terms_source=source,
            availability=Availability.AVAILABLE,
        )

    async def search_products(
        self,
        tenant_id: str,
        client_id: UUID,
        filters: list[ProductFilter],
        universe_ref_id: UUID,
        jurisdiction: str | None = None,
    ) -> tuple[list[Product], str | None, CapabilityState]:
        """Query the approved universe and apply the confirmed filters as given.

        Hard filters are never relaxed; a stale universe ref blocks the search
        instead of silently searching a different catalog.
        """
        self.capability_reason = None
        row = await self._approved_universe(tenant_id, jurisdiction)
        if row is None:
            return [], None, CapabilityState.UNCONFIGURED
        if universe_ref_id is not None and row.id != universe_ref_id:
            self.capability_reason = (
                "The interpretation's product universe is no longer the current "
                "approved universe; search blocked."
            )
            return [], None, CapabilityState.UNAVAILABLE

        definition_ref = to_config_ref(row)
        source = self._source(row)
        products = []
        for record in self._records(row):
            if not self._entitled(record, tenant_id, client_id):
                continue
            if not all(_matches(record, flt) for flt in filters):
                continue
            product = self._to_product(record, definition_ref, source)
            if product is not None:
                products.append(product)
        return products, None, CapabilityState.READY

    async def _find_record(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
        jurisdiction: str | None,
    ) -> tuple[dict, ConfigurationRevision] | None:
        row = await self._approved_universe(tenant_id, jurisdiction)
        if row is None:
            return None
        for record in self._records(row):
            if not self._entitled(record, tenant_id, client_id):
                continue
            ref = record.get("ref")
            if (
                isinstance(ref, dict)
                and str(ref.get("id")) == product_ref.id
                and str(ref.get("version")) == product_ref.version
            ):
                return record, row
        return None

    async def get_product_details(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
        jurisdiction: str | None = None,
    ) -> Product | None:
        """Retrieve a single entitled product by reference."""
        found = await self._find_record(tenant_id, client_id, product_ref, jurisdiction)
        if found is None:
            return None
        record, row = found
        return self._to_product(record, to_config_ref(row), self._source(row))

    async def get_product_record(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
        jurisdiction: str | None = None,
    ) -> dict | None:
        """Raw catalog attributes (complexity, disclosures, objectives) for suitability."""
        found = await self._find_record(tenant_id, client_id, product_ref, jurisdiction)
        return found[0] if found else None
