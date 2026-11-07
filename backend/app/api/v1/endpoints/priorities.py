"""Priority ranking API endpoints per Architecture §6.6.

API-015: POST /books/{book_id}/priority-evaluations - Evaluate book priorities
API-016: GET /books/{book_id}/priority-evaluations/latest - Get latest evaluation
API-053: GET /books/{book_id}/priority-evaluations/{evaluation_id} - Get specific evaluation
API-054: POST /books/{book_id}/priority-controls - Set priority control
API-055: POST /books/{book_id}/contact-outcomes - Record contact outcome
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import check_book_access, check_permission
from app.core.database import get_db
from app.core.identity import get_fixture_principal
from app.schemas.common import Envelope, ResponseMeta
from app.schemas.identity import Principal
from app.schemas.priority import (
    ContactOutcomeRequest,
    ContactOutcomeResponseData,
    ControlResponseData,
    EvaluatePriorityRequest,
    EvaluationData,
    EvaluationStatusData,
    PriorityControlRequest,
)
from app.services.priority import ControlService, RankingService

router = APIRouter(prefix="/books", tags=["priorities"])


@router.post(
    "/{book_id}/priority-evaluations",
    response_model=Envelope[EvaluationData],
    status_code=status.HTTP_201_CREATED,
)
async def evaluate_book_priorities(
    book_id: str,
    request: EvaluatePriorityRequest,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
) -> Envelope[EvaluationData]:
    """Evaluate book-wide priorities per architecture API-015.
    
    Book-scoped evaluation up to 10 unique entitled non-DNC clients with reasons/source/time.
    Empty book returns successful empty evaluation, outage returns 503 not fabricated empty.
    Controls (snooze/dismiss/pin) affect next evaluation only per explicit policy (DEC-03 gated).
    
    Requires: priority:evaluate permission, assigned book
    """
    # Authorization
    check_permission(principal, "priority:evaluate")
    check_book_access(principal, book_id)
    
    # Validate trigger
    if request.trigger not in ["RM_REFRESH", "MATERIAL_SIGNAL"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid trigger"}},
        )
    
    # Service
    ranking_service = RankingService(db)
    
    try:
        evaluation = await ranking_service.evaluate_book_priorities(
            tenant_id=principal.tenant_id,
            book_id=book_id,
            local_date=request.date,
            timezone_str=request.timezone,
            trigger=request.trigger,
            principal_subject=principal.subject,
            policy_config_id=None,  # UNCONFIGURED: DEC-03 external gate
        )
    except Exception as e:
        # Dependency unavailable
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "DEPENDENCY_UNAVAILABLE",
                    "message": f"Ranking evaluation failed: {str(e)}",
                }
            },
        )
    
    return Envelope(
        data=EvaluationData(evaluation=evaluation),
        meta=ResponseMeta(
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=evaluation.evaluated_at,
        ),
    )


@router.get(
    "/{book_id}/priority-evaluations/latest",
    response_model=Envelope[EvaluationStatusData],
)
async def get_latest_priority_evaluation(
    book_id: str,
    date: date,
    timezone: str,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
) -> Envelope[EvaluationStatusData]:
    """Get latest priority evaluation per architecture API-016.
    
    Returns null only if no prior evaluation, not fabricated empty evaluation.
    
    Requires: priority:read permission, assigned book
    """
    # Authorization
    check_permission(principal, "priority:read")
    check_book_access(principal, book_id)
    
    # Service
    ranking_service = RankingService(db)
    evaluation = await ranking_service.get_latest_evaluation(
        tenant_id=principal.tenant_id,
        book_id=book_id,
        local_date=date,
        timezone_str=timezone,
    )
    
    # Determine capability state
    from app.schemas.common import CapabilityState
    capability_state = CapabilityState.READY if evaluation else CapabilityState.UNCONFIGURED
    
    from datetime import datetime, timezone as tz
    return Envelope(
        data=EvaluationStatusData(
            evaluation=evaluation,
            capability_state=capability_state,
        ),
        meta=ResponseMeta(
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=datetime.now(tz.utc),
        ),
    )


@router.get(
    "/{book_id}/priority-evaluations/{evaluation_id}",
    response_model=Envelope[EvaluationData],
)
async def get_priority_evaluation(
    book_id: str,
    evaluation_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
) -> Envelope[EvaluationData]:
    """Get specific priority evaluation per architecture API-053.
    
    Re-filters revoked rows before serialization per architecture.
    
    Requires: priority:read permission, assigned book
    """
    # Authorization
    check_permission(principal, "priority:read")
    check_book_access(principal, book_id)
    
    # Service
    ranking_service = RankingService(db)
    
    # Fetch by ID
    from sqlalchemy import select
    from app.models.priority import PriorityEvaluation as PriorityEvaluationModel, PriorityItem as PriorityItemModel
    
    stmt = select(PriorityEvaluationModel).where(
        PriorityEvaluationModel.id == evaluation_id,
        PriorityEvaluationModel.tenant_id == principal.tenant_id,
        PriorityEvaluationModel.book_id == book_id,
    )
    result = await db.execute(stmt)
    eval_model = result.scalar_one_or_none()
    
    if not eval_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Evaluation not found"}},
        )
    
    # Load items
    items_stmt = select(PriorityItemModel).where(
        PriorityItemModel.evaluation_id == evaluation_id
    ).order_by(PriorityItemModel.rank)
    items_result = await db.execute(items_stmt)
    item_models = items_result.scalars().all()
    
    evaluation = await ranking_service._model_to_dto(eval_model, item_models)
    
    from datetime import datetime, timezone as tz
    return Envelope(
        data=EvaluationData(evaluation=evaluation),
        meta=ResponseMeta(
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=datetime.now(tz.utc),
        ),
    )


@router.post(
    "/{book_id}/priority-controls",
    response_model=Envelope[ControlResponseData],
)
async def set_priority_control(
    book_id: str,
    request: PriorityControlRequest,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
) -> Envelope[ControlResponseData]:
    """Set priority control (snooze/dismiss/pin) per architecture API-054.
    
    Controls persist and affect next evaluation only per explicit policy.
    Controls cannot override eligibility or cap. UNCONFIGURED policy blocks changes.
    
    Requires: priority:control permission, assigned book, DEC-03 policy
    """
    # Authorization
    check_permission(principal, "priority:control")
    check_book_access(principal, book_id)
    
    # Service
    control_service = ControlService(db)
    
    try:
        control, evaluation_state = await control_service.set_priority_control(
            tenant_id=principal.tenant_id,
            book_id=book_id,
            request=request,
            principal_subject=principal.subject,
            policy_config_id=None,  # UNCONFIGURED until DEC-03
        )
    except Exception as e:
        # Policy UNCONFIGURED or validation failed
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "CONFIG_UNCONFIGURED",
                    "message": str(e),
                }
            },
        )
    
    from datetime import datetime, timezone as tz
    return Envelope(
        data=ControlResponseData(
            control=control,
            evaluation_state=evaluation_state,
        ),
        meta=ResponseMeta(
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=datetime.now(tz.utc),
        ),
    )


@router.post(
    "/{book_id}/contact-outcomes",
    response_model=Envelope[ContactOutcomeResponseData],
)
async def record_contact_outcome(
    book_id: str,
    request: ContactOutcomeRequest,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
) -> Envelope[ContactOutcomeResponseData]:
    """Record contact outcome per architecture API-055.
    
    Contact outcomes cannot infer two-way/attendance. DNC still blocks outreach.
    Meaningful touchpoint counted only with approved definition and confirmed evidence.
    
    Requires: outcome:record permission (or priority:control), assigned book
    """
    # Authorization - use priority:control as proxy for outcome recording
    check_permission(principal, "priority:control")
    check_book_access(principal, book_id)
    
    # Validate occurred_at not in future
    from datetime import datetime, timezone as tz
    if request.occurred_at > datetime.now(tz.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "occurred_at cannot be in future"}},
        )
    
    # Service
    control_service = ControlService(db)
    outcome_data = await control_service.record_contact_outcome(
        tenant_id=principal.tenant_id,
        book_id=book_id,
        request=request,
        principal_subject=principal.subject,
    )
    
    return Envelope(
        data=outcome_data,
        meta=ResponseMeta(
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=datetime.now(tz.utc),
        ),
    )
