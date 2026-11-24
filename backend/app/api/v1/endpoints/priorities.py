"""Priority ranking API endpoints per Architecture §6.6.

API-015: POST /books/{book_id}/priority-evaluations - Evaluate book priorities
API-016: GET /books/{book_id}/priority-evaluations/latest - Get latest evaluation
API-053: GET /books/{book_id}/priority-evaluations/{evaluation_id} - Get specific evaluation
API-054: POST /books/{book_id}/priority-controls - Set priority control
API-055: POST /books/{book_id}/contact-outcomes - Record contact outcome
"""
from datetime import date, datetime, UTC, timezone as tz
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import check_book_access, check_permission
from app.core.database import get_db
from app.core.identity import get_fixture_principal
from app.schemas.common import CapabilityState, CatalogRef, Envelope, ResponseMeta
from app.schemas.identity import Principal
from app.schemas.priority import (
    ContactOutcomeRequest,
    ContactOutcomeResponseData,
    ControlResponseData,
    DismissControl,
    EvaluatePriorityRequest,
    EvaluationData,
    EvaluationStatusData,
    PinControl,
    PriorityControlRequest,
    PriorityReasonRef,
    Reason,
    SnoozeControl,
)
from app.services.priority import ControlService, ControlServiceError, RankingService

router = APIRouter(prefix="/books", tags=["priorities"])

# Convenience router for frontend — no book_id required, uses fixture defaults
convenience_router = APIRouter(prefix="/priorities", tags=["priorities"])


class SnoozeBody(BaseModel):
    until: datetime


class PinBody(BaseModel):
    pinned: bool = True


def _convenience_envelope(data: dict) -> dict:
    """Shared data/meta envelope for the frontend convenience routes."""
    return {
        "data": data,
        "meta": {
            "request_id": str(uuid4()),
            "served_at": datetime.now(UTC).isoformat(),
        },
    }


@convenience_router.get("/evaluations")
async def list_priority_evaluations(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
):
    """Real latest evaluation for the principal's entitled books."""
    check_permission(principal, "priority:read")
    evaluation = await RankingService(db).get_latest_evaluation_for_books(
        tenant_id=principal.tenant_id,
        book_ids=[b.book_id for b in principal.books],
    )
    if not evaluation:
        return _convenience_envelope({
            "clients": [],
            "evaluation_date": datetime.now(UTC).date().isoformat(),
            "status": "UNCONFIGURED",
            "capability_state": CapabilityState.UNCONFIGURED.value,
        })

    clients = [
        {
            "client_id": str(item.client.id),
            "name": item.client.name,
            "rank": item.rank,
            "reasons": [
                {
                    "code": r.code,
                    "explanation": r.explanation,
                    "signals": [
                        {"key": s.key, "value": str(s.value.value)}
                        for s in r.signals
                    ],
                }
                for r in item.reasons
            ],
            "controls": [
                {"id": str(c.id), "type": c.request.get("type")}
                for c in item.controls
            ],
        }
        for item in evaluation.items
    ]
    return _convenience_envelope({
        "clients": clients,
        "evaluation_date": evaluation.date.isoformat(),
        "status": evaluation.status.value,
        "capability_state": (
            CapabilityState.READY.value if evaluation.items
            else CapabilityState.UNCONFIGURED.value
        ),
    })


async def _apply_control(
    db: AsyncSession,
    principal: Principal,
    client_id: UUID,
    control_type: str,
    success_status: str,
    until: datetime | None = None,
    pinned: bool = True,
) -> dict:
    """Persist a convenience control against a real stored priority item."""
    check_permission(principal, "priority:control")
    evaluation = await RankingService(db).get_latest_evaluation_for_client(
        tenant_id=principal.tenant_id,
        book_ids=[b.book_id for b in principal.books],
        client_id=client_id,
    )
    if not evaluation or not evaluation.items or not evaluation.items[0].reasons:
        # Controls carry a composite FK to priority_items; without a stored item
        # there is nothing honest to persist.
        return _convenience_envelope({
            "status": "UNCONFIGURED",
            "capability_state": CapabilityState.UNCONFIGURED.value,
            "client_id": str(client_id),
        })

    check_book_access(principal, evaluation.book_id)
    item = evaluation.items[0]
    reason = item.reasons[0]
    if control_type == "SNOOZE":
        control = SnoozeControl(type="SNOOZE", until=until)
    elif control_type == "PIN":
        control = PinControl(type="PIN", pinned=pinned)
    else:
        control = DismissControl(
            type="DISMISS",
            reason=Reason(
                code="RM_DISCRETION",
                catalog_ref=CatalogRef(
                    config_ref=evaluation.policy_ref,
                    catalog_key="RM_DISCRETION",
                ),
            ),
        )

    request = PriorityControlRequest(
        client_id=client_id,
        recommendation_ref=PriorityReasonRef(
            evaluation_id=evaluation.id,
            client_id=client_id,
            reason_key=reason.key,
            reason_hash=reason.hash,
        ),
        control=control,
    )
    try:
        persisted, evaluation_state = await ControlService(db).set_priority_control(
            tenant_id=principal.tenant_id,
            book_id=evaluation.book_id,
            request=request,
            principal_subject=principal.subject,
        )
    except ControlServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "CONFIG_UNCONFIGURED",
                    "message": str(e),
                    "retryable": False,
                }
            },
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "RECOMMENDATION_NOT_FOUND",
                    "message": "The recommendation_ref does not match a stored priority item.",
                    "retryable": False,
                }
            },
        )

    return _convenience_envelope({
        "status": success_status,
        "client_id": str(client_id),
        "control_id": str(persisted.id),
        "evaluation_state": evaluation_state,
        "capability_state": CapabilityState.READY.value,
    })


@convenience_router.post("/{client_id}/snooze")
async def snooze_client(
    client_id: UUID,
    body: SnoozeBody,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
):
    until = body.until if body.until.tzinfo else body.until.replace(tzinfo=UTC)
    if until <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "until must be in the future",
                }
            },
        )
    return await _apply_control(
        db, principal, client_id, "SNOOZE", "snoozed", until=until
    )


@convenience_router.post("/{client_id}/dismiss")
async def dismiss_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
):
    return await _apply_control(db, principal, client_id, "DISMISS", "dismissed")


@convenience_router.post("/{client_id}/pin")
async def pin_client(
    client_id: UUID,
    body: PinBody | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
):
    return await _apply_control(
        db, principal, client_id, "PIN", "pinned",
        pinned=body.pinned if body else True,
    )


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
            request_id=uuid4(),
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
    capability_state = CapabilityState.READY if evaluation else CapabilityState.UNCONFIGURED
    
    return Envelope(
        data=EvaluationStatusData(
            evaluation=evaluation,
            capability_state=capability_state,
        ),
        meta=ResponseMeta(
            request_id=uuid4(),
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
    
    return Envelope(
        data=EvaluationData(evaluation=evaluation),
        meta=ResponseMeta(
            request_id=uuid4(),
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
        )
    except ControlServiceError as e:
        # Policy UNCONFIGURED or the recommendation_ref does not resolve to a
        # stored priority item. Both are actionable client errors, not 500s.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "CONFIG_UNCONFIGURED", "message": str(e), "retryable": False}},
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "RECOMMENDATION_NOT_FOUND",
                    "message": "The recommendation_ref does not match a stored priority item.",
                    "retryable": False,
                }
            },
        )
    
    return Envelope(
        data=ControlResponseData(
            control=control,
            evaluation_state=evaluation_state,
        ),
        meta=ResponseMeta(
            request_id=uuid4(),
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
    if request.occurred_at > datetime.now(tz.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "occurred_at cannot be in future"}},
        )
    
    # Service
    control_service = ControlService(db)
    try:
        outcome_data = await control_service.record_contact_outcome(
            tenant_id=principal.tenant_id,
            book_id=book_id,
            request=request,
            principal_subject=principal.subject,
        )
    except ControlServiceError as e:
        # Explicit guard for fk_contact_outcome_item. Previously this raised an
        # unhandled ForeignKeyViolationError -> bare 500 with no CORS headers,
        # which the browser reported as "Network Error".
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "RECOMMENDATION_NOT_FOUND",
                    "message": str(e),
                    "retryable": False,
                }
            },
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "RECOMMENDATION_NOT_FOUND",
                    "message": "The recommendation_ref does not match a stored priority item.",
                    "retryable": False,
                }
            },
        )

    return Envelope(
        data=outcome_data,
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(tz.utc),
        ),
    )
