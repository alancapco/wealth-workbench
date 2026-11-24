"""Product search, comparison, suitability assessment and override endpoints.

Architecture §6.7 API-056 through API-062.
"""
import json
from datetime import datetime, UTC
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_principal
from app.schemas.identity import Principal
from app.schemas.common import (
    Envelope,
    ResponseMeta,
    Environment,
    EnvironmentKind,
    CapabilityState,
)
from app.schemas.product import (
    ProductInterpretationRequest,
    ProductInterpretationResponse,
    ProductInterpretation,
    EditFiltersRequest,
    ProductSearchRequest,
    ProductSearchResponse,
    ProductSearch,
    ProductComparisonRequest,
    ProductComparisonResponse,
    CandidateSelectionRequest,
    CandidateSelectionResponse,
    AssessmentRequest,
    AssessmentResponse,
    Assessment,
    SuitabilityOverrideRequest,
    SuitabilityOverrideResponse,
    Artifact,
)
from app.schemas.common import ConfigRef, CatalogRef
from app.models.product import CandidateSelection as CandidateSelectionModel
from app.models.platform import ClientScope
from app.models.workflow import Workflow
from app.services.product import (
    ProductSearchService,
    InterpretationService,
    ComparisonService,
    SuitabilityService,
    OverrideService,
)
from app.services.product.artifact_adapter import ProductArtifactRepository
from app.services.product.config_refs import (
    POLICY_CONFIG_CLASS,
    POLICY_CONFIG_KEY,
    PRODUCT_FILTERS_CATALOG_KEY,
    UNIVERSE_CONFIG_CLASS,
    UNIVERSE_CONFIG_KEY,
    parse_config_value,
    resolve_approved_config,
    resolve_client_jurisdiction,
    to_config_ref,
    unconfigured_config_ref,
)

router = APIRouter(prefix="/products", tags=["products"])


async def _resolve_workflow_client(
    db: AsyncSession, workflow_id: UUID, principal: Principal
) -> UUID:
    """Resolve the real client behind a workflow within the caller's tenant.

    A workflow from another tenant and a workflow whose client has no client_scope
    row are indistinguishable from a missing workflow (§3.1). The client_scope
    check also guarantees the composite FK on artifact_lineages is satisfiable.
    """
    row = (await db.execute(
        select(Workflow.tenant_id, Workflow.client_id).where(Workflow.id == workflow_id)
    )).first()
    if row is None or row.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    scope = (await db.execute(
        select(ClientScope.client_id).where(
            ClientScope.tenant_id == principal.tenant_id,
            ClientScope.client_id == row.client_id,
        )
    )).scalar_one_or_none()
    if scope is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return row.client_id


async def _get_universe_config(
    db: AsyncSession, tenant_id: str, jurisdiction: str | None
) -> tuple[ConfigRef, str | None]:
    """Resolve the approved universe ConfigRef with its real content hash."""
    row, reason = await resolve_approved_config(
        db, tenant_id, UNIVERSE_CONFIG_CLASS, UNIVERSE_CONFIG_KEY, jurisdiction
    )
    if row is None:
        return unconfigured_config_ref(
            tenant_id, UNIVERSE_CONFIG_KEY, reason or "Product universe is not configured."
        ), reason
    return to_config_ref(row), None


def _get_catalog_ref(universe_ref: ConfigRef) -> CatalogRef:
    return CatalogRef(config_ref=universe_ref, catalog_key=PRODUCT_FILTERS_CATALOG_KEY)


async def _get_suitability_policy(
    db: AsyncSession, tenant_id: str, jurisdiction: str | None
) -> tuple[ConfigRef | None, dict | None, str | None]:
    """Resolve the approved policy; an absent policy returns an explicit reason."""
    row, reason = await resolve_approved_config(
        db, tenant_id, POLICY_CONFIG_CLASS, POLICY_CONFIG_KEY, jurisdiction
    )
    if row is None:
        return None, None, reason
    policy = parse_config_value(row)
    declared = policy.get("jurisdiction")
    if declared and jurisdiction and declared != jurisdiction:
        return None, None, (
            f"Approved suitability policy is for {declared}, "
            f"not the client's jurisdiction {jurisdiction}."
        )
    return to_config_ref(row), policy, None


@router.post(
    "/{workflow_id}/interpretations",
    response_model=Envelope[ProductInterpretationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def interpret_query(
    workflow_id: UUID,
    request: ProductInterpretationRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[ProductInterpretationResponse]:
    """API-056: Interpret natural language query to structured filters.
    
    Extracts objective, timeframe, amount, risk and other criteria.
    Returns editable confirmed filters. Ambiguities block search until resolved.
    """
    client_id = await _resolve_workflow_client(db, workflow_id, principal)
    jurisdiction = await resolve_client_jurisdiction(db, client_id)

    universe_ref, _ = await _get_universe_config(db, principal.tenant_id, jurisdiction)
    catalog_ref = _get_catalog_ref(universe_ref)
    
    interpretation_service = InterpretationService(universe_ref, catalog_ref)
    interpretation = await interpretation_service.interpret_query(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        query=request.query,
    )
    
    # Persist as artifact
    artifact_repo = ProductArtifactRepository(db)
    artifact_ref = await artifact_repo.create_artifact(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        workflow_id=workflow_id,
        kind="PRODUCT_INTERPRETATION",
        payload=interpretation.model_dump(),
        created_by=principal.subject,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
    )
    
    artifact = Artifact(
        ref=artifact_ref,
        kind="PRODUCT_INTERPRETATION",
        payload=interpretation,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
        created_at=datetime.now(UTC),
    )
    
    return Envelope(
        data=ProductInterpretationResponse(artifact=artifact),
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(UTC),
        ),
    )


@router.patch(
    "/artifacts/{artifact_id}/filters",
    response_model=Envelope[ProductInterpretationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def edit_filters(
    artifact_id: UUID,
    request: EditFiltersRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[ProductInterpretationResponse]:
    """API-057: Edit product filters - hard filters immutable.
    
    Returns new artifact revision with confirmed filters.
    Hard filters (regulatory/policy) cannot be modified.
    """
    # Retrieve existing interpretation artifact
    artifact_repo = ProductArtifactRepository(db)
    existing = await artifact_repo.get_artifact(
        tenant_id=principal.tenant_id,
        artifact_id=artifact_id,
    )
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )
    
    existing_interpretation = ProductInterpretation(**json.loads(existing["payload"]))
    
    # Validate: hard filters cannot be modified
    existing_hard = {f.key: f for f in existing_interpretation.filters if f.hard}
    requested_hard = {f.key: f for f in request.filters if f.hard}
    
    for key, existing_filter in existing_hard.items():
        if key not in requested_hard or requested_hard[key] != existing_filter:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Hard filter '{key}' cannot be modified",
            )
    
    # Create new interpretation with edited filters
    new_interpretation = ProductInterpretation(
        query=existing_interpretation.query,
        filters=request.filters,
        sort_key=request.sort_key,
        universe_ref=existing_interpretation.universe_ref,
        profile_ref=existing_interpretation.profile_ref,
        ambiguities=[],  # Editing resolves ambiguities
    )
    
    # Persist new revision
    artifact_ref = await artifact_repo.create_artifact(
        tenant_id=principal.tenant_id,
        client_id=UUID(existing["client_id"]),
        workflow_id=UUID(existing["workflow_id"]),
        kind="PRODUCT_INTERPRETATION",
        payload=new_interpretation.model_dump(),
        created_by=principal.subject,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
    )
    
    artifact = Artifact(
        ref=artifact_ref,
        kind="PRODUCT_INTERPRETATION",
        payload=new_interpretation,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
        created_at=datetime.now(UTC),
    )
    
    return Envelope(
        data=ProductInterpretationResponse(artifact=artifact),
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(UTC),
        ),
    )


@router.post(
    "/{workflow_id}/searches",
    response_model=Envelope[ProductSearchResponse],
    status_code=status.HTTP_201_CREATED,
)
async def search_products(
    workflow_id: UUID,
    request: ProductSearchRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[ProductSearchResponse]:
    """API-058: Search entitled products with confirmed filters.

    Searches the current approved product universe; without one the result is an
    explicit UNCONFIGURED/UNAVAILABLE explanation rather than fabricated products.
    """
    # Retrieve interpretation artifact
    artifact_repo = ProductArtifactRepository(db)
    interpretation_artifact = await artifact_repo.get_artifact(
        tenant_id=principal.tenant_id,
        artifact_id=request.interpretation_ref.artifact_id,
    )
    
    if not interpretation_artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interpretation artifact not found",
        )
    
    interpretation = ProductInterpretation(**json.loads(interpretation_artifact["payload"]))
    
    # Block search if ambiguities remain
    if interpretation.ambiguities:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ambiguities must be resolved: {', '.join(interpretation.ambiguities)}",
        )
    
    client_id = UUID(interpretation_artifact["client_id"])
    jurisdiction = await resolve_client_jurisdiction(db, client_id)

    search_service = ProductSearchService(
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
        db=db,
    )

    products, next_cursor, capability_state = await search_service.search_products(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        filters=interpretation.filters,
        universe_ref_id=interpretation.universe_ref.id,
        jurisdiction=jurisdiction,
    )

    if capability_state != CapabilityState.READY:
        explanation = search_service.capability_reason or f"Product catalog is {capability_state.value}."
    elif not products:
        explanation = "No entitled products match the confirmed filters."
    else:
        explanation = None

    search_result = ProductSearch(
        interpretation_ref=request.interpretation_ref,
        executed_filters=interpretation.filters,
        executed_at=datetime.now(UTC),
        products=products,
        next_cursor=next_cursor,
        no_result_explanation=explanation,
        soft_edit_suggestions=[],
        sources=list({p.terms_source.id: p.terms_source for p in products}.values()),
    )
    
    # Persist as artifact
    artifact_ref = await artifact_repo.create_artifact(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        workflow_id=workflow_id,
        kind="PRODUCT_SEARCH",
        payload=search_result.model_dump(),
        created_by=principal.subject,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
    )
    
    artifact = Artifact(
        ref=artifact_ref,
        kind="PRODUCT_SEARCH",
        payload=search_result,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
        created_at=datetime.now(UTC),
    )
    
    return Envelope(
        data=ProductSearchResponse(artifact=artifact),
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(UTC),
        ),
    )


@router.post(
    "/{workflow_id}/comparisons",
    response_model=Envelope[ProductComparisonResponse],
    status_code=status.HTTP_201_CREATED,
)
async def compare_products(
    workflow_id: UUID,
    request: ProductComparisonRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[ProductComparisonResponse]:
    """API-059: Compare selected products across metrics.
    
    Returns feature matrix. Missing metrics show null, not fabricated data.
    """
    # Retrieve search artifact
    artifact_repo = ProductArtifactRepository(db)
    search_artifact = await artifact_repo.get_artifact(
        tenant_id=principal.tenant_id,
        artifact_id=request.search_ref.artifact_id,
    )
    
    if not search_artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search artifact not found",
        )
    
    search_result = ProductSearch(**json.loads(search_artifact["payload"]))
    client_id = UUID(search_artifact["client_id"])
    
    # Filter to requested products only
    requested_ids = {(p.id, p.version) for p in request.product_refs}
    selected_products = [
        p for p in search_result.products
        if (p.ref.id, p.ref.version) in requested_ids
    ]
    
    if len(selected_products) != len(request.product_refs):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Some requested products not found in search results",
        )
    
    # Build comparison
    comparison_service = ComparisonService()
    comparison = await comparison_service.compare_products(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        search_ref=request.search_ref,
        products=selected_products,
    )
    
    # Persist as artifact
    artifact_ref = await artifact_repo.create_artifact(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        workflow_id=workflow_id,
        kind="PRODUCT_COMPARISON",
        payload=comparison.model_dump(),
        created_by=principal.subject,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
    )
    
    artifact = Artifact(
        ref=artifact_ref,
        kind="PRODUCT_COMPARISON",
        payload=comparison,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
        created_at=datetime.now(UTC),
    )
    
    return Envelope(
        data=ProductComparisonResponse(artifact=artifact),
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(UTC),
        ),
    )


@router.post(
    "/{workflow_id}/selections",
    response_model=Envelope[CandidateSelectionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def select_candidate(
    workflow_id: UUID,
    request: CandidateSelectionRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CandidateSelectionResponse]:
    """API-060: Record candidate selection for M-08 telemetry.
    
    No trade intent. Selection creates telemetry event only.
    """
    # Retrieve search artifact
    artifact_repo = ProductArtifactRepository(db)
    search_artifact = await artifact_repo.get_artifact(
        tenant_id=principal.tenant_id,
        artifact_id=request.search_ref.artifact_id,
    )
    
    if not search_artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search artifact not found",
        )
    
    client_id = UUID(search_artifact["client_id"])
    
    # Record selection
    selection_id = uuid4()
    now = datetime.now(UTC)
    
    selection = CandidateSelectionModel(
        id=selection_id,
        tenant_id=principal.tenant_id,
        client_id=client_id,
        workflow_id=workflow_id,
        search_revision_id=request.search_ref.revision_id,
        product_id=request.product_ref.id,
        product_version=request.product_ref.version,
        selected_by=principal.subject,
        selected_at=now,
    )
    
    db.add(selection)
    await db.commit()
    
    return Envelope(
        data=CandidateSelectionResponse(
            selection_id=selection_id,
            selected_at=now,
        ),
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(UTC),
        ),
    )


@router.post(
    "/{workflow_id}/assessments",
    response_model=Envelope[AssessmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def assess_suitability(
    workflow_id: UUID,
    request: AssessmentRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[AssessmentResponse]:
    """API-061: Assess product suitability against current profile.

    Returns GREEN/YELLOW/RED/UNAVAILABLE.
    Missing/expired profile blocks GREEN and ticket handoff.
    Pre-screen only, not compliance approval.
    """
    client_id = await _resolve_workflow_client(db, workflow_id, principal)
    jurisdiction = await resolve_client_jurisdiction(db, client_id)

    policy_ref, policy, policy_reason = await _get_suitability_policy(
        db, principal.tenant_id, jurisdiction
    )
    environment = Environment(kind=EnvironmentKind.FIXTURE, id="test")
    suitability_service = SuitabilityService(
        policy_ref,
        db=db,
        policy=policy,
        jurisdiction=jurisdiction,
        policy_reason=policy_reason,
        environment=environment,
    )
    
    assessment = await suitability_service.assess_suitability(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        product_ref=request.product_ref,
        account_ref=request.account_ref,
        amount=request.amount,
    )
    
    # Persist as artifact
    artifact_repo = ProductArtifactRepository(db)
    artifact_ref = await artifact_repo.create_artifact(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        workflow_id=workflow_id,
        kind="ASSESSMENT",
        payload=assessment.model_dump(),
        created_by=principal.subject,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
    )
    
    artifact = Artifact(
        ref=artifact_ref,
        kind="ASSESSMENT",
        payload=assessment,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
        created_at=datetime.now(UTC),
    )
    
    return Envelope(
        data=AssessmentResponse(artifact=artifact),
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(UTC),
        ),
    )


@router.post(
    "/assessments/{assessment_id}/overrides",
    response_model=Envelope[SuitabilityOverrideResponse],
    status_code=status.HTTP_201_CREATED,
)
async def override_assessment(
    assessment_id: UUID,
    request: SuitabilityOverrideRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[SuitabilityOverrideResponse]:
    """API-062: Override soft suitability factors with justification.
    
    Hard stop factors cannot be overridden.
    Requires exact actor, policy, rationale.
    Original rating preserved in audit trail.
    """
    # Retrieve assessment artifact
    artifact_repo = ProductArtifactRepository(db)
    assessment_artifact = await artifact_repo.get_artifact(
        tenant_id=principal.tenant_id,
        artifact_id=assessment_id,
    )
    
    if not assessment_artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment artifact not found",
        )
    
    assessment = Assessment(**json.loads(assessment_artifact["payload"]))
    client_id = UUID(assessment_artifact["client_id"])
    
    # Validate assessment ref matches
    if request.assessment_ref.artifact_id != assessment_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assessment ref does not match endpoint assessment_id",
        )
    
    # Create override
    override_service = OverrideService(db)
    override, blockers = await override_service.create_override(
        tenant_id=principal.tenant_id,
        client_id=client_id,
        actor=principal.subject,
        assessment=assessment,
        assessment_ref=request.assessment_ref,
        factor_keys=request.factor_keys,
        reason=request.reason,
        rationale=request.rationale,
    )
    
    if blockers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Override blocked: {blockers[0].code}",
        )
    
    await db.commit()
    
    return Envelope(
        data=SuitabilityOverrideResponse(override=override),  # type: ignore
        meta=ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(UTC),
        ),
    )
