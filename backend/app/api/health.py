"""Public process and readiness probes (API-017)."""
from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.core.database import check_database

router = APIRouter(tags=["health"])


def _payload(database: bool, schema: bool) -> dict:
    return {
        "status": "UP" if database and schema and settings.identity_configured else "NOT_READY",
        "checks": {
            "database": database,
            "schema": schema,
            "identity_config": settings.identity_configured,
        },
        "environment": settings.APP_ENV,
        "providers": settings.provider_configuration,
    }


@router.get("/health/live")
async def live() -> dict:
    """Process-only liveness probe; it never touches a provider or database."""
    return {
        "status": "UP",
        "checks": {"database": False, "schema": False, "identity_config": False},
        "environment": settings.APP_ENV,
    }


@router.get("/health/ready")
async def ready(response: Response) -> dict:
    database, schema = await check_database()
    payload = _payload(database, schema)
    if payload["status"] != "UP":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
