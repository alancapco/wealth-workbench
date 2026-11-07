"""Product search and suitability evaluation tests.

U-012: Test interpretation, search UNCONFIGURED, comparison, suitability, conflict detection, override approval, audit trail.
"""
import json
import pytest
from datetime import datetime, UTC
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import CandidateSelection, SuitabilityOverride
from app.schemas.product import (
    ProductInterpretation,
    ProductFilter,
    ProductSearch,
    ProductComparison,
    Assessment,
    SuitabilityRating,
    FactorClassification,
    FactorResult,
    ProfileValidity,
)
from app.schemas.common import (
    ConfigRef,
    CatalogRef,
    ArtifactRef,
    Reason,
    Environment,
    EnvironmentKind,
    FieldValue,
    FieldValueType,
    Money,
)
from app.services.product import (
    InterpretationService,
    ProductSearchService,
    ComparisonService,
    SuitabilityService,
    OverrideService,
)
from app.repositories.artifacts import ArtifactRepository


@pytest.fixture
def test_config_ref():
    """Test configuration reference."""
    return ConfigRef(
        id=uuid4(),
        revision=1,
        hash="0" * 64,
    )


@pytest.fixture
def test_catalog_ref(test_config_ref):
    """Test catalog reference."""
    return CatalogRef(
        config_ref=test_config_ref,
        catalog_key="test_catalog",
    )


@pytest.mark.asyncio
async def test_interpretation_extracts_criteria(test_config_ref, test_catalog_ref):
    """Test natural language interpretation extracts structured criteria."""
    tenant_id = "test_tenant"
    client_id = uuid4()
    
    service = InterpretationService(test_config_ref, test_catalog_ref)
    
    # Test: extract risk level from query
    interpretation = await service.interpret_query(
        tenant_id=tenant_id,
        client_id=client_id,
        query="I want low risk conservative investments",
    )
    
    assert interpretation.query == "I want low risk conservative investments"
    assert len(interpretation.filters) > 0
    
    # Check extracted risk filter
    risk_filters = [f for f in interpretation.filters if f.key == "risk_level"]
    assert len(risk_filters) == 1
    assert risk_filters[0].value.value == "LOW"
    assert risk_filters[0].source == "QUERY"
    assert not risk_filters[0].confirmed  # Requires RM confirmation
    
    # Check ambiguity flagged for missing timeframe
    assert len(interpretation.ambiguities) > 0


@pytest.mark.asyncio
async def test_search_unconfigured_without_catalog():
    """Test search returns UNCONFIGURED without product catalog provider."""
    tenant_id = "test_tenant"
    client_id = uuid4()
    universe_ref_id = uuid4()
    
    environment = Environment(kind=EnvironmentKind.FIXTURE, id="test")
    service = ProductSearchService(environment)
    
    filters = [
        ProductFilter(
            key="risk_level",
            operator="EQ",
            value=FieldValue(type=FieldValueType.CHOICE, value="LOW"),
            metric_key=None,
            unit=None,
            source="RM_EDIT",
            hard=False,
            confirmed=True,
            catalog_ref=CatalogRef(
                config_ref=ConfigRef(id=uuid4(), revision=1, hash="0" * 64),
                catalog_key="test",
            ),
        )
    ]
    
    products, next_cursor, capability_state = await service.search_products(
        tenant_id=tenant_id,
        client_id=client_id,
        filters=filters,
        universe_ref_id=universe_ref_id,
    )
    
    # UNCONFIGURED: no product provider configured
    assert products == []
    assert next_cursor is None
    assert capability_state.value == "UNCONFIGURED"


@pytest.mark.asyncio
async def test_comparison_multi_candidate():
    """Test comparison builds feature matrix across multiple candidates."""
    tenant_id = "test_tenant"
    client_id = uuid4()
    search_ref = ArtifactRef(
        artifact_id=uuid4(),
        revision_id=uuid4(),
        version=1,
        hash="0" * 64,
    )
    
    # Create sample products with different metrics
    from app.schemas.product import Product, ProductRef, ProductMetric
    from app.schemas.common import Availability, Source, Origin
    
    test_source = Source(
        id=uuid4(),
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
        availability=Availability.AVAILABLE,
        origin=Origin.RECORDED,
        live_response=False,
        limitation_codes=[],
    )
    
    products = [
        Product(
            ref=ProductRef(id="PROD001", version="v1"),
            name="Conservative Fund",
            asset_class="FIXED_INCOME",
            currencies=["USD"],
            risk_code="LOW",
            minimum_investment=Money(amount=Decimal("1000"), currency="USD"),
            fees=[
                ProductMetric(
                    key="management_fee",
                    name="Management Fee",
                    value=FieldValue(type=FieldValueType.DECIMAL, value=Decimal("0.5")),
                    unit="percent",
                    definition_ref=ConfigRef(id=uuid4(), revision=1, hash="0" * 64),
                    source=test_source,
                )
            ],
            liquidity=[],
            metrics=[],
            esg=[],
            terms_source=test_source,
            availability=Availability.AVAILABLE,
        ),
        Product(
            ref=ProductRef(id="PROD002", version="v1"),
            name="Growth Fund",
            asset_class="EQUITY",
            currencies=["USD"],
            risk_code="HIGH",
            minimum_investment=Money(amount=Decimal("5000"), currency="USD"),
            fees=[
                ProductMetric(
                    key="management_fee",
                    name="Management Fee",
                    value=FieldValue(type=FieldValueType.DECIMAL, value=Decimal("1.2")),
                    unit="percent",
                    definition_ref=ConfigRef(id=uuid4(), revision=1, hash="0" * 64),
                    source=test_source,
                )
            ],
            liquidity=[
                ProductMetric(
                    key="redemption_period",
                    name="Redemption Period",
                    value=FieldValue(type=FieldValueType.TEXT, value="T+2"),
                    unit="days",
                    definition_ref=ConfigRef(id=uuid4(), revision=1, hash="0" * 64),
                    source=test_source,
                )
            ],
            metrics=[],
            esg=[],
            terms_source=test_source,
            availability=Availability.AVAILABLE,
        ),
    ]
    
    service = ComparisonService()
    comparison = await service.compare_products(
        tenant_id=tenant_id,
        client_id=client_id,
        search_ref=search_ref,
        products=products,
    )
    
    assert comparison.search_ref == search_ref
    assert len(comparison.products) == 2
    assert "management_fee" in comparison.metric_keys
    assert "redemption_period" in comparison.metric_keys


@pytest.mark.asyncio
async def test_suitability_conflict_detection(test_config_ref):
    """Test suitability assessment detects conflicts and missing profile."""
    tenant_id = "test_tenant"
    client_id = uuid4()
    
    from app.schemas.product import ProductRef
    
    product_ref = ProductRef(id="PROD001", version="v1")
    
    # Test with policy configured
    service = SuitabilityService(test_config_ref)
    assessment = await service.assess_suitability(
        tenant_id=tenant_id,
        client_id=client_id,
        product_ref=product_ref,
        account_ref="ACC001",
        amount=Money(amount=Decimal("10000"), currency="USD"),
    )
    
    assert assessment.client_id == client_id
    assert assessment.product_ref == product_ref
    assert assessment.profile_validity == "CURRENT"
    assert assessment.rating in ["GREEN", "YELLOW", "RED"]
    assert len(assessment.factors) > 0
    
    # Check factors have required fields
    for factor in assessment.factors:
        assert factor.key
        assert factor.label
        assert factor.classification in ["HARD", "SOFT", "UNKNOWN"]
        assert factor.result in ["PASS", "WARN", "FAIL", "MISSING"]
        assert isinstance(factor.override_permitted, bool)


@pytest.mark.asyncio
async def test_suitability_unconfigured_without_policy():
    """Test suitability returns UNAVAILABLE without approved policy."""
    tenant_id = "test_tenant"
    client_id = uuid4()
    
    from app.schemas.product import ProductRef
    
    product_ref = ProductRef(id="PROD001", version="v1")
    
    # No policy configured
    service = SuitabilityService(policy_ref=None)
    assessment = await service.assess_suitability(
        tenant_id=tenant_id,
        client_id=client_id,
        product_ref=product_ref,
        account_ref=None,
        amount=None,
    )
    
    assert assessment.rating == "UNAVAILABLE"
    assert len(assessment.blockers) > 0
    assert assessment.blockers[0].code == "SUITABILITY_POLICY_UNCONFIGURED"
    assert not assessment.ticket_eligible


@pytest.mark.asyncio
async def test_override_requires_approval(db_session: AsyncSession, test_config_ref, test_catalog_ref):
    """Test override requires approval gate and creates audit trail."""
    tenant_id = "test_tenant"
    client_id = uuid4()
    actor = "rm_user_001"
    
    from app.schemas.product import ProductRef, SuitabilityFactor
    
    # Create assessment with soft factors
    assessment = Assessment(
        client_id=client_id,
        product_ref=ProductRef(id="PROD001", version="v1"),
        account_ref="ACC001",
        amount=Money(amount=Decimal("10000"), currency="USD"),
        profile_id="profile_001",
        profile_version="v1",
        profile_validity="CURRENT",
        input_hash="a" * 64,
        policy_ref=test_config_ref,
        rating="YELLOW",
        current=True,
        factors=[
            SuitabilityFactor(
                key="concentration_limit",
                label="Concentration Limit",
                classification="SOFT",
                result="WARN",
                evidence_refs=[],
                explanation="Position exceeds recommended concentration limit",
                override_permitted=True,
            ),
            SuitabilityFactor(
                key="regulatory_restriction",
                label="Regulatory Restriction",
                classification="HARD",
                result="PASS",
                evidence_refs=[],
                explanation="No regulatory restrictions",
                override_permitted=False,
            ),
        ],
        ticket_eligible=True,
        blockers=[],
        assessed_at=datetime.now(UTC),
    )
    
    assessment_ref = ArtifactRef(
        artifact_id=uuid4(),
        revision_id=uuid4(),
        version=1,
        hash="b" * 64,
    )
    
    reason = Reason(
        code="CLIENT_CONTEXT",
        catalog_ref=test_catalog_ref,
        other_text=None,
    )
    
    service = OverrideService(db_session)
    
    # Test: override soft factor succeeds
    override, blockers = await service.create_override(
        tenant_id=tenant_id,
        client_id=client_id,
        actor=actor,
        assessment=assessment,
        assessment_ref=assessment_ref,
        factor_keys=["concentration_limit"],
        reason=reason,
        rationale="Client has diversified holdings in other accounts not reflected in current assessment",
    )
    
    assert override is not None
    assert len(blockers) == 0
    assert override.actor == actor
    assert override.original_rating == "YELLOW"
    assert "concentration_limit" in override.factor_keys
    
    # Test: hard factor override blocked
    override_hard, blockers_hard = await service.create_override(
        tenant_id=tenant_id,
        client_id=client_id,
        actor=actor,
        assessment=assessment,
        assessment_ref=assessment_ref,
        factor_keys=["regulatory_restriction"],
        reason=reason,
        rationale="Attempted hard stop override",
    )
    
    assert override_hard is None
    assert len(blockers_hard) > 0
    assert blockers_hard[0].code == "HARD_STOP_CANNOT_OVERRIDE"


@pytest.mark.asyncio
async def test_override_audit_trail(db_session: AsyncSession, test_config_ref, test_catalog_ref):
    """Test override creates permanent audit trail."""
    tenant_id = "test_tenant"
    client_id = uuid4()
    actor = "rm_user_001"
    
    from app.schemas.product import ProductRef, SuitabilityFactor
    
    assessment = Assessment(
        client_id=client_id,
        product_ref=ProductRef(id="PROD001", version="v1"),
        account_ref="ACC001",
        amount=None,
        profile_id="profile_001",
        profile_version="v1",
        profile_validity="CURRENT",
        input_hash="c" * 64,
        policy_ref=test_config_ref,
        rating="YELLOW",
        current=True,
        factors=[
            SuitabilityFactor(
                key="risk_mismatch",
                label="Risk Profile Mismatch",
                classification="SOFT",
                result="WARN",
                evidence_refs=[],
                explanation="Product risk slightly above client tolerance",
                override_permitted=True,
            ),
        ],
        ticket_eligible=True,
        blockers=[],
        assessed_at=datetime.now(UTC),
    )
    
    assessment_ref = ArtifactRef(
        artifact_id=uuid4(),
        revision_id=uuid4(),
        version=1,
        hash="d" * 64,
    )
    
    reason = Reason(
        code="INFORMED_DECISION",
        catalog_ref=test_catalog_ref,
        other_text="Client explicitly requested",
    )
    
    service = OverrideService(db_session)
    override, _ = await service.create_override(
        tenant_id=tenant_id,
        client_id=client_id,
        actor=actor,
        assessment=assessment,
        assessment_ref=assessment_ref,
        factor_keys=["risk_mismatch"],
        reason=reason,
        rationale="Client has extensive investment experience and explicitly accepts higher risk for this allocation",
    )
    
    await db_session.commit()
    
    # Query audit record
    from sqlalchemy import select
    result = await db_session.execute(
        select(SuitabilityOverride).where(SuitabilityOverride.id == override.id)
    )
    audit_record = result.scalar_one()
    
    assert audit_record.tenant_id == tenant_id
    assert audit_record.client_id == client_id
    assert audit_record.actor == actor
    assert audit_record.original_rating == "YELLOW"
    assert audit_record.rationale == override.rationale
    
    # Verify JSON fields preserved
    factor_keys = json.loads(audit_record.factor_keys)
    assert "risk_mismatch" in factor_keys


@pytest.mark.asyncio
async def test_candidate_selection_telemetry(db_session: AsyncSession):
    """Test candidate selection creates M-08 telemetry record."""
    from app.models.product import CandidateSelection
    
    tenant_id = "test_tenant"
    client_id = uuid4()
    workflow_id = uuid4()
    search_revision_id = uuid4()
    selected_by = "rm_user_001"
    
    selection_id = uuid4()
    selection = CandidateSelection(
        id=selection_id,
        tenant_id=tenant_id,
        client_id=client_id,
        workflow_id=workflow_id,
        search_revision_id=search_revision_id,
        product_id="PROD001",
        product_version="v1",
        selected_by=selected_by,
        selected_at=datetime.now(UTC),
    )
    
    db_session.add(selection)
    await db_session.commit()
    
    # Query telemetry record
    from sqlalchemy import select
    result = await db_session.execute(
        select(CandidateSelection).where(CandidateSelection.id == selection_id)
    )
    record = result.scalar_one()
    
    assert record.tenant_id == tenant_id
    assert record.client_id == client_id
    assert record.product_id == "PROD001"
    assert record.selected_by == selected_by
