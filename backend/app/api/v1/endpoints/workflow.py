"""Workflow API endpoints per Architecture §6.2 (API-007..009, 025..030)."""
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import Envelope, ResponseMeta
from app.schemas.workflow import (
    AbandonWorkflowRequest,
    PauseWorkflowRequest,
    ResumeWorkflowRequest,
    RunStageRequest,
    SkillListData,
    StartWorkflow,
    StageRun,
    Workflow,
    WorkflowListData,
    WorkflowStatus,
)
from app.services.workflow import SkillRegistry, StageRunner, WorkflowOrchestrator

router = APIRouter()

# Mock principal for testing (would come from session middleware)
MOCK_TENANT = "test-tenant"
MOCK_ACTOR = "test-rm"
MOCK_PERMISSIONS = ["workflow:start", "workflow:read", "workflow:run", "workflow:manage"]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: StartWorkflow,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Create workflow per API-007.
    
    Freezes client context at creation.
    Returns 201 with workflow.
    """
    try:
        orchestrator = WorkflowOrchestrator(db)
        workflow = await orchestrator.create_workflow(
            tenant_id=MOCK_TENANT,
            request=request,
            actor=MOCK_ACTOR,
        )
        
        # Convert to response DTO (simplified - full impl maps all fields)
        workflow_dto = Workflow(
            id=workflow.id,
            type=request.type,
            client_id=workflow.client_id,
            meeting_id=workflow.meeting_id,
            status=WorkflowStatus(workflow.status),
            row_version=workflow.row_version,
            context_revision=workflow.context_revision,
            entry=workflow.entry_point,
            current_stage=workflow.current_stage,
            stages=[],  # Would populate from stage_runs in full impl
            action_ids=[],
            last_confirmed_at=workflow.created_at,
            next_decision=None,
        )
        
        return Envelope(
            data={"workflow": workflow_dto},
            meta=ResponseMeta(
                request_id=uuid4(),
                served_at=datetime.utcnow(),
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Get workflow per API-008.
    
    GET never starts run - read-only.
    """
    try:
        orchestrator = WorkflowOrchestrator(db)
        workflow = await orchestrator.get_workflow(
            tenant_id=MOCK_TENANT,
            workflow_id=workflow_id,
        )
        
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        
        workflow_dto = Workflow(
            id=workflow.id,
            type=WorkflowStatus(workflow.workflow_type),  # Would use WorkflowType
            client_id=workflow.client_id,
            meeting_id=workflow.meeting_id,
            status=WorkflowStatus(workflow.status),
            row_version=workflow.row_version,
            context_revision=workflow.context_revision,
            entry=workflow.entry_point,
            current_stage=workflow.current_stage,
            stages=[],
            action_ids=[],
            last_confirmed_at=workflow.updated_at,
            next_decision=None,
        )
        
        return Envelope(
            data={"workflow": workflow_dto},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("")
async def list_workflows(
    book_id: str = Query(...),
    status_filter: WorkflowStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> Envelope[WorkflowListData]:
    """List workflows per API-025."""
    try:
        orchestrator = WorkflowOrchestrator(db)
        workflows = await orchestrator.list_workflows(
            tenant_id=MOCK_TENANT,
            book_id=book_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        
        workflow_dtos = [
            Workflow(
                id=w.id,
                type=WorkflowStatus(w.workflow_type),
                client_id=w.client_id,
                meeting_id=w.meeting_id,
                status=WorkflowStatus(w.status),
                row_version=w.row_version,
                context_revision=w.context_revision,
                entry=w.entry_point,
                current_stage=w.current_stage,
                stages=[],
                action_ids=[],
                last_confirmed_at=w.updated_at,
                next_decision=None,
            )
            for w in workflows
        ]
        
        return Envelope(
            data=WorkflowListData(items=workflow_dtos, next_cursor=None),
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{workflow_id}/stages/{stage_key}/runs", status_code=status.HTTP_202_ACCEPTED)
async def run_stage(
    workflow_id: UUID,
    stage_key: str,
    request: RunStageRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Run stage per API-009.
    
    Validates context revision - rejects stale context.
    Returns 202 with stage run.
    """
    try:
        runner = StageRunner(db)
        
        # In full impl, would lookup skill from registry
        skill_id = stage_key
        skill_version = "1.0.0"
        
        run = await runner.create_stage_run(
            tenant_id=MOCK_TENANT,
            workflow_id=workflow_id,
            stage_key=stage_key,
            request=request,
            skill_id=skill_id,
            skill_version=skill_version,
            actor=MOCK_ACTOR,
        )
        
        run_dto = StageRun(
            id=run.id,
            workflow_id=run.workflow_id,
            stage_key=run.stage_key,
            status=run.status,  # Would use StageStatus enum
            input_refs=request.input_refs,
            output_refs=[],
            context_revision=run.context_revision,
            skill_id=run.skill_id,
            skill_version=run.skill_version,
            started_at=run.started_at,
            completed_at=run.completed_at,
            manual_intervention=run.manual_intervention,
            error_code=run.error_code,
        )
        
        return Envelope(
            data={"run": run_dto},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        if "Context revision mismatch" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "CONTEXT_CHANGED", "message": str(e)}
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: UUID,
    request: PauseWorkflowRequest,
    if_match: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Pause workflow per API-026."""
    try:
        orchestrator = WorkflowOrchestrator(db)
        workflow = await orchestrator.pause_workflow(
            tenant_id=MOCK_TENANT,
            workflow_id=workflow_id,
            request=request,
            actor=MOCK_ACTOR,
            if_match=if_match,
        )
        
        workflow_dto = Workflow(
            id=workflow.id,
            type=WorkflowStatus(workflow.workflow_type),
            client_id=workflow.client_id,
            meeting_id=workflow.meeting_id,
            status=WorkflowStatus(workflow.status),
            row_version=workflow.row_version,
            context_revision=workflow.context_revision,
            entry=workflow.entry_point,
            current_stage=workflow.current_stage,
            stages=[],
            action_ids=[],
            last_confirmed_at=workflow.updated_at,
            next_decision=None,
        )
        
        return Envelope(
            data={"workflow": workflow_dto},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        if "ETag mismatch" in str(e):
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail={"code": "VERSION_MISMATCH", "message": str(e)}
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{workflow_id}/resume")
async def resume_workflow(
    workflow_id: UUID,
    request: ResumeWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Resume workflow per API-027.
    
    Reauthorizes without auto-running.
    """
    try:
        orchestrator = WorkflowOrchestrator(db)
        workflow = await orchestrator.resume_workflow(
            tenant_id=MOCK_TENANT,
            workflow_id=workflow_id,
            request=request,
            actor=MOCK_ACTOR,
        )
        
        workflow_dto = Workflow(
            id=workflow.id,
            type=WorkflowStatus(workflow.workflow_type),
            client_id=workflow.client_id,
            meeting_id=workflow.meeting_id,
            status=WorkflowStatus(workflow.status),
            row_version=workflow.row_version,
            context_revision=workflow.context_revision,
            entry=workflow.entry_point,
            current_stage=workflow.current_stage,
            stages=[],
            action_ids=[],
            last_confirmed_at=workflow.updated_at,
            next_decision=None,
        )
        
        return Envelope(
            data={"workflow": workflow_dto},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{workflow_id}/abandon")
async def abandon_workflow(
    workflow_id: UUID,
    request: AbandonWorkflowRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Abandon workflow per API-028.
    
    Does not unsend/cancel dispatched actions.
    """
    try:
        orchestrator = WorkflowOrchestrator(db)
        workflow, continuing_action_ids = await orchestrator.abandon_workflow(
            tenant_id=MOCK_TENANT,
            workflow_id=workflow_id,
            request=request,
            actor=MOCK_ACTOR,
        )
        
        workflow_dto = Workflow(
            id=workflow.id,
            type=WorkflowStatus(workflow.workflow_type),
            client_id=workflow.client_id,
            meeting_id=workflow.meeting_id,
            status=WorkflowStatus(workflow.status),
            row_version=workflow.row_version,
            context_revision=workflow.context_revision,
            entry=workflow.entry_point,
            current_stage=workflow.current_stage,
            stages=[],
            action_ids=[],
            last_confirmed_at=workflow.updated_at,
            next_decision=None,
        )
        
        return Envelope(
            data={"workflow": workflow_dto, "continuing_action_ids": continuing_action_ids},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{workflow_id}/runs/{run_id}")
async def get_stage_run(
    workflow_id: UUID,
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Get stage run per API-029."""
    try:
        runner = StageRunner(db)
        run = await runner.get_stage_run(
            tenant_id=MOCK_TENANT,
            run_id=run_id,
        )
        
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage run not found")
        
        run_dto = StageRun(
            id=run.id,
            workflow_id=run.workflow_id,
            stage_key=run.stage_key,
            status=run.status,
            input_refs=[],  # Would load from stage_artifact_refs
            output_refs=[],
            context_revision=run.context_revision,
            skill_id=run.skill_id,
            skill_version=run.skill_version,
            started_at=run.started_at,
            completed_at=run.completed_at,
            manual_intervention=run.manual_intervention,
            error_code=run.error_code,
        )
        
        return Envelope(
            data={"run": run_dto},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/skills")
async def list_skills(
    db: AsyncSession = Depends(get_db),
) -> Envelope[SkillListData]:
    """List skills per API-030.
    
    Only visible allowed skills returned.
    """
    try:
        registry = SkillRegistry(db)
        skills = await registry.list_skills(
            tenant_id=MOCK_TENANT,
            permissions=MOCK_PERMISSIONS,
        )
        
        return Envelope(
            data=SkillListData(items=skills, next_cursor=None),
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
