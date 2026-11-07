"""Admin configuration, audit, and telemetry schemas."""
from datetime import datetime, UTC
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Scope


class DecisionGate(BaseModel):
    """Decision gate status (DEC-01 through DEC-08)."""
    model_config = ConfigDict(extra="forbid")

    key: str
    scope: Scope
    enabled: bool
    updated_at: datetime | None = None


class AuditEventDetail(BaseModel):
    """Audit event detail for critical operations."""
    model_config = ConfigDict(extra="forbid")

    id: UUID
    timestamp: datetime
    principal: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any]
    client_id: UUID | None = None
    workflow_id: UUID | None = None
    correlation_id: UUID


class TelemetryMetric(BaseModel):
    """Telemetry metric result."""
    model_config = ConfigDict(extra="forbid")

    metric_name: str
    labels: dict[str, Any]
    value: float
    timestamp: datetime


class AuditLogQuery(BaseModel):
    """Audit log query filters."""
    model_config = ConfigDict(extra="forbid")

    time_range: tuple[datetime, datetime] | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    limit: int = Field(default=100, gt=0, le=1000)


class MetricQueryRequest(BaseModel):
    """Metric query request."""
    model_config = ConfigDict(extra="forbid")

    metric_name: str
    from_time: datetime
    to_time: datetime
    environment_kind: str | None = None


class MetricQueryResponse(BaseModel):
    """Metric query response with aggregated stats."""
    model_config = ConfigDict(extra="forbid")

    metric_name: str
    time_range: dict[str, datetime]
    count: int
    sum: float | None = None
    avg: float | None = None
    min: float | None = None
    max: float | None = None


class DecisionGateList(BaseModel):
    """List of decision gates."""
    model_config = ConfigDict(extra="forbid")

    gates: list[DecisionGate]


class AuditLogResponse(BaseModel):
    """Audit log query response."""
    model_config = ConfigDict(extra="forbid")

    events: list[AuditEventDetail]
    total: int
