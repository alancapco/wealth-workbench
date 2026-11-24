"""Session endpoint - current session info (API-001)."""
from fastapi import APIRouter, Depends
from uuid import uuid4

from app.api.dependencies import CurrentPrincipal
from app.schemas.common import Envelope, ResponseMeta
from app.schemas.identity import Principal

router = APIRouter(tags=["session"])


@router.get("/session")
async def get_current_session(
    principal: CurrentPrincipal,
) -> Envelope[dict]:
    """Get current session info (API-001).
    
    Returns authenticated principal with device state, books, and tenant context.
    """
    return Envelope(
        data={
            "subject": principal.subject,
            "tenant_id": principal.tenant_id,
            "display_name": principal.display_name,
            "permissions": principal.permissions,
            "books": [{"book_id": b.book_id, "display_name": b.display_name} for b in principal.books],
            "entitlement_revision": principal.entitlement_revision,
            "session_expires_at": principal.session_expires_at.isoformat(),
            "environment": {
                "kind": principal.environment.kind,
                "id": principal.environment.id,
            },
            "device_state": principal.device_state,
        },
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=principal.session_expires_at,
        ),
    )
