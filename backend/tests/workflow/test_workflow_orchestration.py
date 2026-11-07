"""Test workflow orchestration per U-006 acceptance criteria.

Tests:
- Context freeze on workflow launch
- Stage idempotency (same run_id on retry)
- Stale context rejection (context_revision mismatch)
- Pause/resume workflow
- Abandon workflow
- GET never starts run
"""
import pytest
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClientScope, Workflow, StageRun
from app.schemas.workflow import (
    StartWorkflow,
    WorkflowEntry,
    WorkflowType,
    RunStageRequest,
    PauseWorkflowRequest,
    ResumeWorkflowRequest,
    AbandonWorkflowRequest,
)
from app.schemas.common import ArtifactRef
from app.services.workflow import WorkflowOrchestrator, StageRunner


@pytest.fixture
async def client_scope(db_session: AsyncSession) -> ClientScope:
    """Create test client scope with context_revision."""
    from app.models import WorkbenchTenant
    
    tenant = WorkbenchTenant(
        tenant_id="test-tenant",
        environment_kind="FIXTURE",
        environment_id="test-env"
    )
    db_session.add(tenant)
    
    # Create client
    from app.models import Client
    client = Client(
        id=uuid4(),
        name="Test Client",
        email="test@example.com"
    )
    db_session.add(client)
    await db_session.flush()
    
    # Create client scope
    scope = ClientScope(
        tenant_id="test-tenant",
        client_id=client.id,
        context_revision=1,
        ownership_source="test",
        ownership_version="1.0",
        verified_at=datetime.now(UTC)
    )
    db_session.add(scope)
    await db_session.commit()
    
    return scope


@pytest.mark.asyncio
async def test_workflow_context_freeze(db_session: AsyncSession, client_scope: ClientScope):
    """Test workflow creation freezes context_revision."""
    orchestrator = WorkflowOrchestrator(db_session)
    
    request = StartWorkflow(
        type=WorkflowType.MEETING_PREP,
        client_id=client_scope.client_id,
        meeting_id=None,
        meeting=None,
        entry=WorkflowEntry.MY_DAY,
        resume_workflow_id=None,
        task_context="Test workflow"
    )
    
    workflow = await orchestrator.create_workflow(
        tenant_id="test-tenant",
        request=request,
        actor="test-rm"
    )
    
    # Assert context frozen at creation
    assert workflow.context_revision == client_scope.context_revision
    assert workflow.context_revision == 1
    
    # Update client context revision
    client_scope.context_revision = 2
    await db_session.commit()
    
    # Workflow context_revision should remain frozen
    await db_session.refresh(workflow)
    assert workflow.context_revision == 1, "Context should remain frozen"


@pytest.mark.asyncio
async def test_stage_run_idempotency(db_session: AsyncSession, client_scope: ClientScope):
    """Test stage run with same stage_key creates new version on retry."""
    orchestrator = WorkflowOrchestrator(db_session)
    runner = StageRunner(db_session)
    
    # Create workflow
    workflow_req = StartWorkflow(
        type=WorkflowType.MEETING_PREP,
        client_id=client_scope.client_id,
        entry=WorkflowEntry.MY_DAY
    )
    workflow = await orchestrator.create_workflow("test-tenant", workflow_req, "test-rm")
    
    # Create first stage run
    run_req = RunStageRequest(
        input_refs=[],
        context_revision=workflow.context_revision
    )
    
    run1 = await runner.create_stage_run(
        tenant_id="test-tenant",
        workflow_id=workflow.id,
        stage_key="brief.generate",
        request=run_req,
        skill_id="brief.generate",
        skill_version="1.0.0",
        actor="test-rm"
    )
    
    assert run1.stage_version == 1
    assert run1.status == "PENDING"
    
    # Idempotency: same stage_key returns existing run if not failed
    run2 = await runner.create_stage_run(
        tenant_id="test-tenant",
        workflow_id=workflow.id,
        stage_key="brief.generate",
        request=run_req,
        skill_id="brief.generate",
        skill_version="1.0.0",
        actor="test-rm"
    )
    
    assert run2.id == run1.id, "Should return existing run"
    assert run2.stage_version == 1
    
    # Mark first run as failed
    run1.status = "FAILED"
    await db_session.commit()
    
    # Retry creates new version
    run3 = await runner.create_stage_run(
        tenant_id="test-tenant",
        workflow_id=workflow.id,
        stage_key="brief.generate",
        request=run_req,
        skill_id="brief.generate",
        skill_version="1.0.0",
        actor="test-rm"
    )
    
    assert run3.id != run1.id, "Retry should create new run"
    assert run3.stage_version == 2, "Should increment version"


@pytest.mark.asyncio
async def test_stale_context_rejection(db_session: AsyncSession, client_scope: ClientScope):
    """Test stage run rejects stale context_revision."""
    orchestrator = WorkflowOrchestrator(db_session)
    runner = StageRunner(db_session)
    
    # Create workflow with context_revision=1
    workflow_req = StartWorkflow(
        type=WorkflowType.MEETING_PREP,
        client_id=client_scope.client_id,
        entry=WorkflowEntry.MY_DAY
    )
    workflow = await orchestrator.create_workflow("test-tenant", workflow_req, "test-rm")
    assert workflow.context_revision == 1
    
    # Try to run stage with stale context_revision
    run_req = RunStageRequest(
        input_refs=[],
        context_revision=999  # Stale!
    )
    
    with pytest.raises(ValueError, match="Context revision mismatch"):
        await runner.create_stage_run(
            tenant_id="test-tenant",
            workflow_id=workflow.id,
            stage_key="brief.generate",
            request=run_req,
            skill_id="brief.generate",
            skill_version="1.0.0",
            actor="test-rm"
        )


@pytest.mark.asyncio
async def test_pause_resume_workflow(db_session: AsyncSession, client_scope: ClientScope):
    """Test workflow pause and resume."""
    orchestrator = WorkflowOrchestrator(db_session)
    
    # Create and start workflow
    workflow_req = StartWorkflow(
        type=WorkflowType.MEETING_PREP,
        client_id=client_scope.client_id,
        entry=WorkflowEntry.MY_DAY
    )
    workflow = await orchestrator.create_workflow("test-tenant", workflow_req, "test-rm")
    
    # Set to RUNNING
    workflow.status = "RUNNING"
    await db_session.commit()
    
    # Pause workflow
    etag = f'"{workflow.id}:{workflow.row_version}"'
    pause_req = PauseWorkflowRequest(reason="Testing pause")
    paused = await orchestrator.pause_workflow(
        tenant_id="test-tenant",
        workflow_id=workflow.id,
        request=pause_req,
        actor="test-rm",
        if_match=etag
    )
    
    assert paused.status == "PAUSED"
    assert paused.row_version == 2
    
    # Resume workflow
    resume_req = ResumeWorkflowRequest()
    resumed = await orchestrator.resume_workflow(
        tenant_id="test-tenant",
        workflow_id=workflow.id,
        request=resume_req,
        actor="test-rm"
    )
    
    assert resumed.status == "NOT_STARTED", "Resume transitions to NOT_STARTED"
    assert resumed.row_version == 3


@pytest.mark.asyncio
async def test_abandon_workflow(db_session: AsyncSession, client_scope: ClientScope):
    """Test workflow abandon."""
    orchestrator = WorkflowOrchestrator(db_session)
    
    workflow_req = StartWorkflow(
        type=WorkflowType.MEETING_PREP,
        client_id=client_scope.client_id,
        entry=WorkflowEntry.MY_DAY
    )
    workflow = await orchestrator.create_workflow("test-tenant", workflow_req, "test-rm")
    
    # Abandon workflow
    abandon_req = AbandonWorkflowRequest(confirmation=True, reason="Test abandon")
    abandoned, continuing_actions = await orchestrator.abandon_workflow(
        tenant_id="test-tenant",
        workflow_id=workflow.id,
        request=abandon_req,
        actor="test-rm"
    )
    
    assert abandoned.status == "ABANDONED"
    assert isinstance(continuing_actions, list)


@pytest.mark.asyncio
async def test_get_workflow_never_starts_run(db_session: AsyncSession, client_scope: ClientScope):
    """Test GET workflow is read-only, never starts run."""
    orchestrator = WorkflowOrchestrator(db_session)
    
    workflow_req = StartWorkflow(
        type=WorkflowType.MEETING_PREP,
        client_id=client_scope.client_id,
        entry=WorkflowEntry.MY_DAY
    )
    workflow = await orchestrator.create_workflow("test-tenant", workflow_req, "test-rm")
    
    initial_status = workflow.status
    initial_updated = workflow.updated_at
    
    # GET workflow multiple times
    for _ in range(3):
        fetched = await orchestrator.get_workflow("test-tenant", workflow.id)
        assert fetched is not None
        assert fetched.status == initial_status
        assert fetched.updated_at == initial_updated, "GET should not modify workflow"
    
    # Verify no stage runs created
    stmt = select(StageRun).where(StageRun.workflow_id == workflow.id)
    result = await db_session.execute(stmt)
    runs = result.scalars().all()
    assert len(runs) == 0, "GET should never create stage runs"
