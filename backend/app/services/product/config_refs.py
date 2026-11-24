"""Resolve product universe / suitability policy references from approved configuration.

ConfigRefs must point at real, approved configuration revisions. The frozen DTO
contract still requires a ConfigRef when nothing is approved, so the fallback is a
deterministic, content-addressed reference whose payload explicitly says
UNCONFIGURED and why -- never a random id or an all-zero hash.
"""
import hashlib
import json
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import ConfigurationRevision
from app.models.client_data import DemoClient
from app.models.models import Client
from app.schemas.common import ConfigRef, Scope
from app.services.config.config_service import ConfigService

UNIVERSE_CONFIG_CLASS = "CATALOG"
UNIVERSE_CONFIG_KEY = "product.universe"
POLICY_CONFIG_CLASS = "GOVERNANCE"
POLICY_CONFIG_KEY = "suitability.policy"
PRODUCT_FILTERS_CATALOG_KEY = "product_filters"


def canonical_json(payload: dict) -> str:
    # Same canonical form as MessageService/ActionService/brief generator and the
    # artifact PATCH endpoint, so artifact hashes compare across the whole chain.
    # default=str only affects non-JSON values (Decimal, UUID, datetime) in
    # product payloads; JSON-native content hashes identically everywhere.
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)


def canonical_hash(payload: dict) -> str:
    """SHA-256 over canonical JSON, shared by product config/assessment hashing."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


JURISDICTION_CODES = {
    "HK": "HK", "HONG KONG": "HK", "HONG KONG SAR": "HK",
    "SG": "SG", "SINGAPORE": "SG",
    "CN": "CN", "CHINA": "CN", "MAINLAND CHINA": "CN",
    "JP": "JP", "JAPAN": "JP",
    "AU": "AU", "AUSTRALIA": "AU",
    "IN": "IN", "INDIA": "IN",
    "GB": "GB", "UNITED KINGDOM": "GB",
}


def jurisdiction_code(value: str | None) -> str | None:
    return JURISDICTION_CODES.get((value or "").strip().upper())


async def resolve_client_jurisdiction(db: AsyncSession, client_id: UUID) -> str | None:
    """Market code from the client's real country/region, used to pick the rule set."""
    country = (await db.execute(
        select(DemoClient.country).where(DemoClient.id == client_id)
    )).scalar_one_or_none()
    if not country:
        country = (await db.execute(
            select(Client.region).where(Client.id == client_id)
        )).scalar_one_or_none()
    return jurisdiction_code(country)


async def resolve_approved_config(
    db: AsyncSession,
    tenant_id: str,
    config_class: str,
    config_key: str,
    jurisdiction: str | None = None,
) -> tuple[ConfigurationRevision | None, str | None]:
    """Return the highest-revision APPROVED config for the narrowest matching scope.

    Jurisdiction-scoped configuration wins over tenant-wide configuration so the
    same product logic can serve several markets without embedding their rules.
    """
    service = ConfigService(db)
    scopes = [Scope(tenant_id=tenant_id, jurisdiction=jurisdiction)] if jurisdiction else []
    scopes.append(Scope(tenant_id=tenant_id))
    try:
        for scope in scopes:
            rows = await service.list_active_configs(scope)
            matches = [
                row for row in rows
                if row.status == "APPROVED"
                and row.config_class == config_class
                and row.config_key == config_key
            ]
            if matches:
                row = max(matches, key=lambda r: r.revision)
                if not row.content_hash or row.content_hash == "0" * 64:
                    return None, f"APPROVED {config_key} configuration has no valid content hash"
                try:
                    json.loads(row.value)
                except (TypeError, ValueError):
                    return None, f"APPROVED {config_key} configuration value is not valid JSON"
                return row, None
    except Exception as exc:
        # A configuration read failure is an honest UNAVAILABLE, not a silent None.
        return None, f"Could not read approved {config_key} configuration: {type(exc).__name__}"

    scope_note = f" for jurisdiction {jurisdiction}" if jurisdiction else ""
    return None, f"No APPROVED {config_key} configuration for tenant {tenant_id}{scope_note}"


def to_config_ref(row: ConfigurationRevision) -> ConfigRef:
    """Map a real configuration revision to its ConfigRef (real id/revision/hash)."""
    return ConfigRef(id=row.id, revision=row.revision, hash=row.content_hash)


def parse_config_value(row: ConfigurationRevision) -> dict:
    value = json.loads(row.value)
    return value if isinstance(value, dict) else {}


def unconfigured_config_ref(tenant_id: str, config_key: str, reason: str) -> ConfigRef:
    """Deterministic reference for an unconfigured capability.

    The DTO contract forbids a null ConfigRef. Deriving both the id and the hash
    from an explicit UNCONFIGURED document keeps the reference stable and honest
    instead of inventing an approved configuration that does not exist.
    """
    return ConfigRef(
        id=uuid5(NAMESPACE_URL, f"rm-workbench:{tenant_id}:{config_key}:unconfigured"),
        revision=1,
        hash=canonical_hash({
            "tenant_id": tenant_id,
            "config_key": config_key,
            "status": "UNCONFIGURED",
            "reason": reason,
        }),
    )
