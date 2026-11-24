"""Active RANKING configuration lookup shared by the priority and client ranking services."""
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import ConfigurationRevision
from app.schemas.common import ConfigRef, Scope
from app.services.config.config_service import ConfigService

RANKING_CONFIG_CLASS = "RANKING"
DEFAULT_CONCENTRATION_THRESHOLD = 0.10


async def get_active_ranking_config(
    db: AsyncSession,
    tenant_id: str,
    book_id: str | None = None,
) -> ConfigurationRevision | None:
    """Highest-revision approved RANKING config; book scope falls back to tenant scope."""
    config_service = ConfigService(db)
    scopes = [Scope(tenant_id=tenant_id, book_id=book_id)] if book_id else []
    scopes.append(Scope(tenant_id=tenant_id))
    for scope in scopes:
        configs = [
            c for c in await config_service.list_active_configs(scope)
            if c.config_class == RANKING_CONFIG_CLASS
        ]
        if configs:
            return max(configs, key=lambda c: (c.revision, c.created_at))
    return None


def config_ref(config: ConfigurationRevision) -> ConfigRef:
    """ConfigRef from stored revision data; hash the stored value if the hash is not canonical hex."""
    content_hash = config.content_hash
    if len(content_hash) != 64 or not all(c in "0123456789abcdef" for c in content_hash):
        content_hash = hashlib.sha256(config.value.encode()).hexdigest()
    return ConfigRef(id=config.id, revision=config.revision, hash=content_hash)


async def get_config_ref(db: AsyncSession, config_id) -> ConfigRef | None:
    """ConfigRef for a stored revision id, or None when the revision does not exist."""
    config = await db.get(ConfigurationRevision, config_id)
    return config_ref(config) if config else None


async def get_concentration_threshold(db: AsyncSession, tenant_id: str | None) -> float:
    """Concentration threshold from the approved RANKING config, else the documented default."""
    if tenant_id:
        try:
            config = await get_active_ranking_config(db, tenant_id)
            if config:
                raw = json.loads(config.value).get("concentration_threshold")
                if isinstance(raw, (int, float)) and not isinstance(raw, bool) and 0 < raw <= 1:
                    return float(raw)
        except Exception:
            # Config lookup must not disable ranking in a partially configured environment.
            pass
    return DEFAULT_CONCENTRATION_THRESHOLD
