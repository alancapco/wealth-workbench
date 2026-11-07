"""Telemetry service for performance monitoring and metrics."""
import json
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import TelemetryEvent
from app.schemas.common import Environment


class TelemetryService:
    """Service for recording telemetry and querying metrics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_telemetry(
        self,
        tenant_id: str,
        event_type: str,
        environment: Environment,
        actor_safe_id: str,
        correlation_id: UUID,
        labels: dict,
        value: float,
        timestamp: Optional[datetime] = None,
        book_id: Optional[str] = None,
        client_id: Optional[UUID] = None,
        workflow_id: Optional[UUID] = None,
        revision_id: Optional[UUID] = None,
    ) -> TelemetryEvent:
        """
        Record telemetry event for performance monitoring.
        
        Captures:
        - API latency
        - Workflow stage duration
        - Ranking evaluation time
        - Selection counts (M-08)
        """
        event = TelemetryEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            book_id=book_id,
            client_id=client_id,
            workflow_id=workflow_id,
            revision_id=revision_id,
            environment_kind=environment.kind.value,
            environment_id=environment.id,
            event_name=event_type,
            actor_safe_id=actor_safe_id,
            correlation_id=correlation_id,
            occurred_at=timestamp or datetime.now(UTC),
            version_tags=json.dumps(labels),
            measures=json.dumps({"value": value}),
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def query_metrics(
        self,
        tenant_id: str,
        metric_name: str,
        from_time: datetime,
        to_time: datetime,
        environment_kind: Optional[str] = None,
    ) -> dict:
        """
        Query aggregated metrics for a time range.
        
        Returns: count, sum, avg, min, max for the metric.
        """
        query = select(
            func.count(TelemetryEvent.id).label("count"),
            func.sum(
                func.cast(
                    func.json_extract_path_text(TelemetryEvent.measures, "value"),
                    func.Float,
                )
            ).label("sum"),
            func.avg(
                func.cast(
                    func.json_extract_path_text(TelemetryEvent.measures, "value"),
                    func.Float,
                )
            ).label("avg"),
            func.min(
                func.cast(
                    func.json_extract_path_text(TelemetryEvent.measures, "value"),
                    func.Float,
                )
            ).label("min"),
            func.max(
                func.cast(
                    func.json_extract_path_text(TelemetryEvent.measures, "value"),
                    func.Float,
                )
            ).label("max"),
        ).where(
            TelemetryEvent.tenant_id == tenant_id,
            TelemetryEvent.event_name == metric_name,
            TelemetryEvent.occurred_at >= from_time,
            TelemetryEvent.occurred_at <= to_time,
        )

        if environment_kind:
            query = query.where(TelemetryEvent.environment_kind == environment_kind)

        result = await self.session.execute(query)
        row = result.one()

        return {
            "metric_name": metric_name,
            "time_range": {"from": from_time, "to": to_time},
            "count": row.count or 0,
            "sum": float(row.sum) if row.sum else None,
            "avg": float(row.avg) if row.avg else None,
            "min": float(row.min) if row.min else None,
            "max": float(row.max) if row.max else None,
        }
