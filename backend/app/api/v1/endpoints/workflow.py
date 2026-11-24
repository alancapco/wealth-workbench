"""Workflow API endpoints per Architecture §6.2 (API-007..009, 025..030)."""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.identity import FIXTURE_TENANT_ID
from app.models import (
    ActionAuthorization,
    ActionPreview,
    ArtifactLineage,
    ArtifactRevision,
    OutboxAction,
    StageArtifactRef,
    StageRun as StageRunModel,
    Workflow as WorkflowModel,
)
from app.schemas.common import ArtifactRef, Envelope, ResponseMeta
from app.schemas.workflow import (
    AbandonWorkflowRequest,
    PauseWorkflowRequest,
    ResumeWorkflowRequest,
    RunStageRequest,
    SkillListData,
    StartWorkflow,
    StageRun,
    StageStatus,
    StageSummary,
    Workflow,
    WorkflowListData,
    WorkflowStatus,
    WorkflowType,
)
from app.services.workflow import SkillRegistry, StageRunner, WorkflowOrchestrator

router = APIRouter()

# Fixture principal. This used to be "test-tenant", which matched no row in
# workbench_tenants/client_scope, so every workflow read returned an empty list
# even when workflows were seeded. Align with the rest of the fixture data.
MOCK_TENANT = FIXTURE_TENANT_ID
MOCK_ACTOR = "test-rm"
MOCK_PERMISSIONS = ["workflow:start", "workflow:read", "workflow:run", "workflow:manage"]


async def _load_stage_refs(
    db: AsyncSession,
    tenant_id: str,
    run_ids: set[UUID],
) -> dict[UUID, tuple[list[ArtifactRef], list[ArtifactRef]]]:
    """Load INPUT/OUTPUT artifact refs of stage runs from the persisted link table."""
    refs: dict[UUID, tuple[list[ArtifactRef], list[ArtifactRef]]] = {
        run_id: ([], []) for run_id in run_ids
    }
    if not run_ids:
        return refs

    rows = (await db.execute(
        select(StageArtifactRef.run_id, StageArtifactRef.direction, ArtifactRevision)
        .join(ArtifactRevision, and_(
            ArtifactRevision.tenant_id == StageArtifactRef.tenant_id,
            ArtifactRevision.client_id == StageArtifactRef.client_id,
            ArtifactRevision.id == StageArtifactRef.revision_id,
        ))
        .where(
            StageArtifactRef.tenant_id == tenant_id,
            StageArtifactRef.run_id.in_(run_ids),
        )
    )).all()
    for run_id, direction, revision in rows:
        ref = ArtifactRef(
            artifact_id=revision.artifact_id,
            revision_id=revision.id,
            version=revision.version,
            hash=revision.content_hash,
        )
        inputs, outputs = refs[run_id]
        (inputs if direction == "INPUT" else outputs).append(ref)
    return refs


async def _load_workflow_details(
    db: AsyncSession,
    tenant_id: str,
    workflow_ids: list[UUID],
) -> tuple[dict[UUID, list[StageSummary]], dict[UUID, list[UUID]]]:
    """Load real stage summaries and dispatched action IDs for the given workflows."""
    stages: dict[UUID, list[StageSummary]] = {wid: [] for wid in workflow_ids}
    actions: dict[UUID, list[UUID]] = {wid: [] for wid in workflow_ids}
    if not workflow_ids:
        return stages, actions

    runs = (await db.execute(
        select(StageRunModel)
        .where(
            StageRunModel.tenant_id == tenant_id,
            StageRunModel.workflow_id.in_(workflow_ids),
        )
        .order_by(StageRunModel.stage_key, StageRunModel.stage_version)
    )).scalars().all()

    refs_by_run = await _load_stage_refs(db, tenant_id, {run.id for run in runs})
    for run in runs:
        inputs, outputs = refs_by_run[run.id]
        stages[run.workflow_id].append(StageSummary(
            key=run.stage_key,
            status=StageStatus(run.status),
            run_id=run.id,
            skill_id=run.skill_id,
            skill_version=run.skill_version,
            artifact_refs=inputs + outputs,
            blockers=[],
        ))

    # An action is linked to a workflow through the artifact revision it was
    # previewed against: outbox -> authorization -> preview -> revision -> lineage.
    rows = (await db.execute(
        select(OutboxAction.id, ArtifactLineage.workflow_id)
        .join(ActionAuthorization, and_(
            ActionAuthorization.tenant_id == OutboxAction.tenant_id,
            ActionAuthorization.client_id == OutboxAction.client_id,
            ActionAuthorization.id == OutboxAction.authorization_id,
        ))
        .join(ActionPreview, and_(
            ActionPreview.tenant_id == ActionAuthorization.tenant_id,
            ActionPreview.client_id == ActionAuthorization.client_id,
            ActionPreview.id == ActionAuthorization.preview_id,
        ))
        .join(ArtifactRevision, and_(
            ArtifactRevision.tenant_id == ActionPreview.tenant_id,
            ArtifactRevision.client_id == ActionPreview.client_id,
            ArtifactRevision.id == ActionPreview.revision_id,
        ))
        .join(ArtifactLineage, and_(
            ArtifactLineage.tenant_id == ArtifactRevision.tenant_id,
            ArtifactLineage.client_id == ArtifactRevision.client_id,
            ArtifactLineage.id == ArtifactRevision.artifact_id,
        ))
        .where(
            OutboxAction.tenant_id == tenant_id,
            ArtifactLineage.workflow_id.in_(workflow_ids),
        )
    )).all()
    for action_id, workflow_id in rows:
        actions[workflow_id].append(action_id)
    return stages, actions


def _to_workflow_dto(
    workflow: WorkflowModel,
    stages: list[StageSummary],
    action_ids: list[UUID],
    last_confirmed_at: datetime,
) -> Workflow:
    return Workflow(
        id=workflow.id,
        type=WorkflowType(workflow.workflow_type),
        client_id=workflow.client_id,
        meeting_id=workflow.meeting_id,
        status=WorkflowStatus(workflow.status),
        row_version=workflow.row_version,
        context_revision=workflow.context_revision,
        entry=workflow.entry_point,
        current_stage=workflow.current_stage,
        stages=stages,
        action_ids=action_ids,
        last_confirmed_at=last_confirmed_at,
        next_decision=None,
    )


async def _workflow_dto(
    db: AsyncSession,
    workflow: WorkflowModel,
    last_confirmed_at: datetime,
) -> Workflow:
    stages, actions = await _load_workflow_details(db, workflow.tenant_id, [workflow.id])
    return _to_workflow_dto(
        workflow, stages[workflow.id], actions[workflow.id], last_confirmed_at
    )


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
        
        workflow_dto = await _workflow_dto(db, workflow, workflow.created_at)
        
        return Envelope(
            data={"workflow": workflow_dto},
            meta=ResponseMeta(
                request_id=uuid4(),
                served_at=datetime.now(UTC),
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ``:uuid`` keeps this route from shadowing the literal ``/skills`` route below.
# Without the converter, "skills" is parsed as a workflow_id and raises 422.
@router.get("/{workflow_id:uuid}")
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
        
        workflow_dto = await _workflow_dto(db, workflow, workflow.updated_at)
        
        return Envelope(
            data={"workflow": workflow_dto},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
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
        
        stages, actions = await _load_workflow_details(
            db, MOCK_TENANT, [w.id for w in workflows]
        )
        workflow_dtos = [
            _to_workflow_dto(w, stages[w.id], actions[w.id], w.updated_at)
            for w in workflows
        ]
        
        return Envelope(
            data=WorkflowListData(items=workflow_dtos, next_cursor=None),
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
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
        registry = SkillRegistry(db)

        skill = await registry.get_skill_for_stage(MOCK_TENANT, stage_key)
        if skill is None:
            raise ValueError(f"Skill {stage_key} is not registered for tenant {MOCK_TENANT}")

        run = await runner.create_stage_run(
            tenant_id=MOCK_TENANT,
            workflow_id=workflow_id,
            stage_key=stage_key,
            request=request,
            skill_id=skill.skill_id,
            skill_version=skill.version,
            actor=MOCK_ACTOR,
        )

        refs = await _load_stage_refs(db, MOCK_TENANT, {run.id})
        input_refs, output_refs = refs[run.id]
        run_dto = StageRun(
            id=run.id,
            workflow_id=run.workflow_id,
            stage_key=run.stage_key,
            status=StageStatus(run.status),
            input_refs=input_refs,
            output_refs=output_refs,
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
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
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
        
        workflow_dto = await _workflow_dto(db, workflow, workflow.updated_at)
        
        return Envelope(
            data={"workflow": workflow_dto},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
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
        
        workflow_dto = await _workflow_dto(db, workflow, workflow.updated_at)
        
        return Envelope(
            data={"workflow": workflow_dto},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
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
        
        workflow_dto = await _workflow_dto(db, workflow, workflow.updated_at)
        
        return Envelope(
            data={"workflow": workflow_dto, "continuing_action_ids": continuing_action_ids},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
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
        
        refs = await _load_stage_refs(db, MOCK_TENANT, {run.id})
        input_refs, output_refs = refs[run.id]
        run_dto = StageRun(
            id=run.id,
            workflow_id=run.workflow_id,
            stage_key=run.stage_key,
            status=StageStatus(run.status),
            input_refs=input_refs,
            output_refs=output_refs,
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
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
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
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
