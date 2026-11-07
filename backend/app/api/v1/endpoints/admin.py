"""Admin configuration, audit, and telemetry endpoints (API-070 through API-073)."""
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.admin import (
    AuditEventDetail,
    AuditLogResponse,
    DecisionGate,
    DecisionGateList,
    MetricQueryRequest,
    MetricQueryResponse,
)
from app.schemas.common import Envelope, ResponseMeta, Scope
from app.services.config import AuditService, ConfigService, TelemetryService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/config/gates", response_model=Envelope[DecisionGateList])
async def list_decision_gates(
    tenant_id: str = Query(..., description="Tenant ID for scope"),
    book_id: str | None = Query(None, description="Book ID for scope"),
    jurisdiction: str | None = Query(None, description="Jurisdiction for scope"),
    db: AsyncSession = Depends(get_db),
) -> Envelope[DecisionGateList]:
    """
    API-070: List all decision gates for a scope.
    
    Returns the status of all DEC-01 through DEC-08 decision gates.
    """
    scope = Scope(tenant_id=tenant_id, book_id=book_id, jurisdiction=jurisdiction)
    config_service = ConfigService(db)

    # Decision gates: DEC-01 through DEC-08
    gate_keys = [
        "DEC-01",  # Brief
        "DEC-02",  # Messaging
        "DEC-03",  # Calendar
        "DEC-04",  # Product/Suitability
        "DEC-05",  # Shariah
        "DEC-06",  # Family
        "DEC-07",  # Household
        "DEC-08",  # Mobile
    ]

    gates = []
    for key in gate_keys:
        enabled = await config_service.get_decision_gate(scope, key)
        gates.append(
            DecisionGate(
                key=key,
                scope=scope,
                enabled=enabled,
                updated_at=datetime.utcnow(),
            )
        )

    return Envelope(
        data=DecisionGateList(gates=gates),
        meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow()),
    )


@router.get("/config/gates/{key}", response_model=Envelope[DecisionGate])
async def get_decision_gate(
    key: str,
    tenant_id: str = Query(..., description="Tenant ID for scope"),
    book_id: str | None = Query(None, description="Book ID for scope"),
    jurisdiction: str | None = Query(None, description="Jurisdiction for scope"),
    db: AsyncSession = Depends(get_db),
) -> Envelope[DecisionGate]:
    """
    API-071: Get specific decision gate status.
    
    Returns enabled status for a specific gate (defaults to False if not configured).
    """
    scope = Scope(tenant_id=tenant_id, book_id=book_id, jurisdiction=jurisdiction)
    config_service = ConfigService(db)

    enabled = await config_service.get_decision_gate(scope, key)

    gate = DecisionGate(
        key=key,
        scope=scope,
        enabled=enabled,
        updated_at=datetime.utcnow(),
    )

    return Envelope(
        data=gate,
        meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow()),
    )


@router.get("/audit", response_model=Envelope[AuditLogResponse])
async def query_audit_log(
    tenant_id: str = Query(..., description="Tenant ID (required for tenant scoping)"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    action: str | None = Query(None, description="Filter by action"),
    from_time: datetime | None = Query(None, description="Start of time range"),
    to_time: datetime | None = Query(None, description="End of time range"),
    limit: int = Query(100, gt=0, le=1000, description="Max results"),
    db: AsyncSession = Depends(get_db),
) -> Envelope[AuditLogResponse]:
    """
    API-072: Query audit log with filters (tenant-scoped, requires admin permission).
    
    Returns audit events for critical operations:
    - workflow start/pause/abandon
    - artifact approval/rejection
    - action execution
    - config change
    - consent withdrawal
    """
    audit_service = AuditService(db)

    events = await audit_service.query_audit_log(
        tenant_id=tenant_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        from_time=from_time,
        to_time=to_time,
        limit=limit,
    )

    # Convert to response DTOs
    event_details = [
        AuditEventDetail(
            id=event.id,
            timestamp=event.occurred_at,
            principal=event.actor,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            details=event.safe_details if isinstance(event.safe_details, dict) else {},
            client_id=event.client_id,
            workflow_id=event.workflow_id,
            correlation_id=event.correlation_id,
        )
        for event in events
    ]

    return Envelope(
        data=AuditLogResponse(events=event_details, total=len(event_details)),
        meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow()),
    )


@router.get("/telemetry/metrics", response_model=Envelope[MetricQueryResponse])
async def query_metrics(
    metric_name: str = Query(..., description="Metric name to query"),
    from_time: datetime = Query(..., description="Start of time range"),
    to_time: datetime = Query(..., description="End of time range"),
    tenant_id: str = Query(..., description="Tenant ID (required)"),
    environment_kind: str | None = Query(None, description="Filter by environment kind"),
    db: AsyncSession = Depends(get_db),
) -> Envelope[MetricQueryResponse]:
    """
    API-073: Query metrics (requires admin permission).
    
    Returns aggregated telemetry metrics:
    - API latency
    - Workflow stage duration
    - Ranking evaluation time
    - Selection counts (M-08)
    """
    telemetry_service = TelemetryService(db)

    metrics = await telemetry_service.query_metrics(
        tenant_id=tenant_id,
        metric_name=metric_name,
        from_time=from_time,
        to_time=to_time,
        environment_kind=environment_kind,
    )

    response = MetricQueryResponse(
        metric_name=metrics["metric_name"],
        time_range=metrics["time_range"],
        count=metrics["count"],
        sum=metrics["sum"],
        avg=metrics["avg"],
        min=metrics["min"],
        max=metrics["max"],
    )

    return Envelope(
        data=response,
        meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow()),
    )
