"""Telemetry endpoint (API-074)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4

from app.api.dependencies import CurrentPrincipal, VerifiedCSRF
from app.core.database import get_db
from app.services.config.telemetry_service import TelemetryService

router = APIRouter(tags=["telemetry"])


class TelemetryEventRequest(BaseModel):
    """Request to record telemetry event."""
    event_type: str
    labels: dict
    value: float
    book_id: str | None = None
    client_id: UUID | None = None
    workflow_id: UUID | None = None
    revision_id: UUID | None = None


@router.post("/telemetry/events")
async def record_telemetry_event(
    event: TelemetryEventRequest,
    principal: CurrentPrincipal,
    csrf: VerifiedCSRF,
    db: AsyncSession = Depends(get_db),
):
    """Record telemetry event (API-074).
    
    Captures performance metrics:
    - API latency
    - Workflow stage duration
    - Ranking evaluation time
    - Selection counts
    """
    service = TelemetryService(db)
    
    await service.record_telemetry(
        tenant_id=principal.tenant_id,
        event_type=event.event_type,
        environment=principal.environment,
        actor_safe_id=principal.subject,
        correlation_id=uuid4(),
        labels=event.labels,
        value=event.value,
        book_id=event.book_id,
        client_id=event.client_id,
        workflow_id=event.workflow_id,
        revision_id=event.revision_id,
    )
    
    await db.commit()
    
    return {"status": "recorded"}
