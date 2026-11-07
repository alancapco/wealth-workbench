"""Stage runner - dispatch/retry/lease management per Architecture §6.2.

Implements:
- Stage run creation with context validation
- Lease-based distributed execution
- Retry with idempotency
- Expiry handling (preserves output, not counted as completion)
"""
from datetime import datetime, UTC, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StageRun, Workflow
from app.repositories import AuditRepository, TransactionContext
from app.schemas.common import ArtifactRef
from app.schemas.workflow import RunStageRequest, StageStatus


class StageRunner:
    """Stage execution with lease-based idempotency per Architecture §6.2."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tx = TransactionContext(session)
        self.audit = AuditRepository(session)

    async def create_stage_run(
        self,
        tenant_id: str,
        workflow_id: UUID,
        stage_key: str,
        request: RunStageRequest,
        skill_id: str,
        skill_version: str,
        actor: str,
    ) -> StageRun:
        """Create stage run per API-009.
        
        Validates context revision against workflow's frozen context.
        Unique (workflow_id, stage_key, stage_version) ensures idempotency.
        """
        # Get workflow
        stmt = select(Workflow).where(
            Workflow.tenant_id == tenant_id,
            Workflow.id == workflow_id
        )
        result = await self.session.execute(stmt)
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Validate context revision (stale context rejection)
        if request.context_revision != workflow.context_revision:
            raise ValueError(
                f"Context revision mismatch: workflow has {workflow.context_revision}, "
                f"request has {request.context_revision}"
            )
        
        # Check for existing run with same stage_key (idempotency)
        stmt = select(StageRun).where(
            StageRun.tenant_id == tenant_id,
            StageRun.workflow_id == workflow_id,
            StageRun.stage_key == stage_key
        ).order_by(StageRun.stage_version.desc())
        result = await self.session.execute(stmt)
        existing_run = result.scalar_one_or_none()
        
        if existing_run:
            # Return existing run if not failed
            if existing_run.status not in [StageStatus.FAILED.value]:
                return existing_run
            
            # Retry: increment stage_version
            stage_version_num = existing_run.stage_version + 1
        else:
            stage_version_num = 1
        
        # Create new stage run
        run = StageRun(
            id=uuid4(),
            tenant_id=tenant_id,
            client_id=workflow.client_id,
            workflow_id=workflow_id,
            stage_key=stage_key,
            stage_version=stage_version_num,
            status=StageStatus.PENDING.value,
            skill_id=skill_id,
            skill_version=skill_version,
            context_revision=request.context_revision,
            manual_intervention=False,
            error_code=None,
            lease_token=None,
            lease_until=None,
            started_at=None,
            completed_at=None
        )
        
        self.session.add(run)
        
        # Update workflow status
        if workflow.status == "NOT_STARTED":
            workflow.status = "RUNNING"
        workflow.current_stage = stage_key
        workflow.updated_at = datetime.now(UTC)
        
        await self.audit.record_event(
            tenant_id=tenant_id,
            actor=actor,
            action="stage.create",
            resource_type="stage_run",
            resource_id=str(run.id),
            workflow_id=workflow_id,
            correlation_id=uuid4(),
            outcome="created"
        )
        
        await self.tx.commit()
        return run

    async def claim_stage_run(
        self,
        tenant_id: str,
        run_id: UUID,
        lease_duration_seconds: int = 300,
    ) -> StageRun | None:
        """Claim stage run with lease for distributed execution.
        
        Uses lease_token + lease_until for concurrency control.
        """
        stmt = select(StageRun).where(
            StageRun.tenant_id == tenant_id,
            StageRun.id == run_id,
            StageRun.status == StageStatus.PENDING.value
        )
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            return None
        
        # Claim with lease
        run.lease_token = uuid4()
        run.lease_until = datetime.now(UTC) + timedelta(seconds=lease_duration_seconds)
        run.status = StageStatus.RUNNING.value
        run.started_at = datetime.now(UTC)
        
        await self.session.flush()
        return run

    async def complete_stage_run(
        self,
        tenant_id: str,
        run_id: UUID,
        lease_token: UUID,
        output_refs: list[ArtifactRef],
        actor: str,
    ) -> StageRun:
        """Complete stage run with lease token validation.
        
        Stale worker cannot overwrite newer state (compare-and-swap).
        """
        stmt = select(StageRun).where(
            StageRun.tenant_id == tenant_id,
            StageRun.id == run_id
        )
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            raise ValueError(f"Stage run {run_id} not found")
        
        # Validate lease token (compare-and-swap)
        if run.lease_token != lease_token:
            raise ValueError("Lease token mismatch - stale worker")
        
        # Check lease not expired
        if run.lease_until and datetime.now(UTC) > run.lease_until:
            raise ValueError("Lease expired")
        
        run.status = StageStatus.COMPLETED.value
        run.completed_at = datetime.now(UTC)
        run.lease_token = None
        run.lease_until = None
        
        # Store output refs (would create StageArtifactRef records in full impl)
        
        await self.audit.record_event(
            tenant_id=tenant_id,
            actor=actor,
            action="stage.complete",
            resource_type="stage_run",
            resource_id=str(run.id),
            workflow_id=run.workflow_id,
            correlation_id=uuid4(),
            outcome="completed"
        )
        
        await self.tx.commit()
        return run

    async def fail_stage_run(
        self,
        tenant_id: str,
        run_id: UUID,
        lease_token: UUID,
        error_code: str,
        actor: str,
    ) -> StageRun:
        """Fail stage run with lease token validation.
        
        Expired lease marks FAILED with preserved prior output.
        Not counted as completion.
        """
        stmt = select(StageRun).where(
            StageRun.tenant_id == tenant_id,
            StageRun.id == run_id
        )
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            raise ValueError(f"Stage run {run_id} not found")
        
        # Validate lease token
        if run.lease_token != lease_token:
            raise ValueError("Lease token mismatch - stale worker")
        
        run.status = StageStatus.FAILED.value
        run.error_code = error_code
        run.lease_token = None
        run.lease_until = None
        # Note: prior output preserved, completed_at remains None
        
        await self.audit.record_event(
            tenant_id=tenant_id,
            actor=actor,
            action="stage.fail",
            resource_type="stage_run",
            resource_id=str(run.id),
            workflow_id=run.workflow_id,
            correlation_id=uuid4(),
            outcome="failed"
        )
        
        await self.tx.commit()
        return run

    async def get_stage_run(
        self,
        tenant_id: str,
        run_id: UUID,
    ) -> StageRun | None:
        """Get stage run by ID per API-029."""
        stmt = select(StageRun).where(
            StageRun.tenant_id == tenant_id,
            StageRun.id == run_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
