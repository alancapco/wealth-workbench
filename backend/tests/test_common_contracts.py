"""Test common DTO contracts - envelope, provenance, validation.

Architecture §3.2, §5 - frozen contracts verification.
"""
from datetime import datetime, UTC, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.common import (
    ArtifactRef,
    Availability,
    Blocker,
    BlockerResolution,
    Capability,
    CapabilityState,
    CatalogRef,
    Completeness,
    ConfigRef,
    Envelope,
    Environment,
    EnvironmentKind,
    EvidenceLocation,
    EvidenceLocationKind,
    EvidenceRef,
    FieldValue,
    FieldValueType,
    ItemRef,
    MappedValue,
    Money,
    Origin,
    Reason,
    Region,
    ResponseMeta,
    Review,
    ReviewDecision,
    ReviewItem,
    ReviewScope,
    ReviewState,
    Scope,
    Source,
)


class TestEnvelope:
    """Test response envelope structure."""
    
    def test_envelope_with_simple_data(self):
        """Envelope wraps arbitrary data with meta."""
        meta = ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(timezone.utc),
            next_cursor=None,
        )
        envelope = Envelope[dict](
            data={"test": "value"},
            meta=meta,
        )
        
        assert envelope.data == {"test": "value"}
        assert envelope.meta.request_id == meta.request_id
        assert envelope.meta.next_cursor is None
    
    def test_envelope_forbids_extra_fields(self):
        """Architecture §5: extra=forbid on all DTOs."""
        meta = ResponseMeta(
            request_id=uuid4(),
            served_at=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValidationError) as exc_info:
            Envelope[dict](
                data={"test": "value"},
                meta=meta,
                unknown_field="should fail",  # type: ignore
            )
        
        errors = exc_info.value.errors()
        assert any("extra" in str(e).lower() or "unexpected" in str(e).lower() for e in errors)


class TestProvenanceDimensions:
    """Test independent provenance dimensions per architecture §3.2."""
    
    def test_environment_fixture(self):
        """Fixture environment for isolated tests."""
        env = Environment(kind=EnvironmentKind.FIXTURE, id="test-fixture-01")
        assert env.kind == EnvironmentKind.FIXTURE
        assert env.id == "test-fixture-01"
    
    def test_environment_production(self):
        """Production environment."""
        env = Environment(kind=EnvironmentKind.PRODUCTION, id="prod-us-east-1")
        assert env.kind == EnvironmentKind.PRODUCTION
    
    def test_source_independent_dimensions(self):
        """Source has environment, availability, origin as separate dimensions."""
        source = Source(
            id=uuid4(),
            environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
            availability=Availability.STALE,
            origin=Origin.RECORDED,
            live_response=False,
            limitation_codes=["PARTIAL_COVERAGE"],
        )
        
        # Architecture §3.2: STALE and live_response may coexist
        assert source.availability == Availability.STALE
        assert source.origin == Origin.RECORDED
        assert source.live_response is False
        assert "PARTIAL_COVERAGE" in source.limitation_codes
    
    def test_source_live_response_requires_evidence(self):
        """live_response=true is server-issued only with receipt."""
        source = Source(
            id=uuid4(),
            environment=Environment(kind=EnvironmentKind.PRODUCTION, id="prod"),
            availability=Availability.AVAILABLE,
            origin=Origin.RECORDED,
            live_response=True,
            adapter_receipt_id="receipt-xyz-123",
            as_of=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
        )
        
        assert source.live_response is True
        assert source.adapter_receipt_id is not None
        assert source.as_of is not None
    
    def test_source_derived_origin(self):
        """Derived material cites exact input sources."""
        source = Source(
            id=uuid4(),
            environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
            availability=Availability.AVAILABLE,
            origin=Origin.DERIVED,
            live_response=False,
            system_key="model:gpt-4",
            record_version="v1.2.3",
        )
        
        assert source.origin == Origin.DERIVED
        assert source.system_key == "model:gpt-4"
    
    def test_evidence_location_transcript(self):
        """Evidence location for transcript segment."""
        evidence = EvidenceLocation(
            kind=EvidenceLocationKind.TRANSCRIPT,
            segment_id=uuid4(),
            excerpt="Client mentioned...",
        )
        
        assert evidence.kind == EvidenceLocationKind.TRANSCRIPT
        assert evidence.segment_id is not None
        assert evidence.excerpt is not None
    
    def test_evidence_location_rm_entry(self):
        """Evidence location for RM-entered data."""
        evidence = EvidenceLocation(
            kind=EvidenceLocationKind.RM_ENTRY,
            entered_by="rm001@example.com",
        )
        
        assert evidence.kind == EvidenceLocationKind.RM_ENTRY
        assert evidence.entered_by is not None


class TestRegion:
    """Test Region wrapper for values with availability/capability state."""
    
    def test_region_available_complete(self):
        """Region with available complete data."""
        region = Region[list[str]](
            availability=Availability.AVAILABLE,
            completeness=Completeness.COMPLETE,
            capability_state=CapabilityState.READY,
            as_of=datetime.now(timezone.utc),
            value=["item1", "item2"],
            sources=[],
        )
        
        assert region.availability == Availability.AVAILABLE
        assert region.completeness == Completeness.COMPLETE
        assert region.capability_state == CapabilityState.READY
        assert len(region.value) == 2
    
    def test_region_unavailable_with_error(self):
        """Region unavailable with error code."""
        region = Region[None](
            availability=Availability.UNAVAILABLE,
            completeness=Completeness.EMPTY,
            capability_state=CapabilityState.UNAVAILABLE,
            as_of=None,
            value=None,
            sources=[],
            error_code="PROVIDER_TIMEOUT",
        )
        
        assert region.availability == Availability.UNAVAILABLE
        assert region.error_code == "PROVIDER_TIMEOUT"
        assert region.value is None
    
    def test_region_empty_not_unavailable(self):
        """Successful zero result is EMPTY, not UNAVAILABLE."""
        region = Region[list](
            availability=Availability.AVAILABLE,
            completeness=Completeness.EMPTY,
            capability_state=CapabilityState.READY,
            as_of=datetime.now(timezone.utc),
            value=[],
            sources=[],
        )
        
        assert region.availability == Availability.AVAILABLE
        assert region.completeness == Completeness.EMPTY
        assert region.value == []


class TestScopeAndConfig:
    """Test scope and configuration references."""
    
    def test_scope_tenant_only(self):
        """Scope with tenant only."""
        scope = Scope(tenant_id="TENANT_001")
        assert scope.tenant_id == "TENANT_001"
        assert scope.book_id is None
        assert scope.jurisdiction is None
    
    def test_scope_tenant_book_jurisdiction(self):
        """Scope with all three dimensions."""
        scope = Scope(
            tenant_id="TENANT_001",
            book_id="BOOK_ALPHA",
            jurisdiction="US-NY",
        )
        
        assert scope.tenant_id == "TENANT_001"
        assert scope.book_id == "BOOK_ALPHA"
        assert scope.jurisdiction == "US-NY"
    
    def test_config_ref_hash_validation(self):
        """ConfigRef hash must be 64 lowercase hex."""
        valid_hash = "a" * 64
        config_ref = ConfigRef(id=uuid4(), revision=1, hash=valid_hash)
        assert config_ref.hash == valid_hash
    
    def test_config_ref_rejects_uppercase_hash(self):
        """Hash must be lowercase hex."""
        with pytest.raises(ValidationError):
            ConfigRef(id=uuid4(), revision=1, hash="A" * 64)
    
    def test_config_ref_rejects_short_hash(self):
        """Hash must be exactly 64 characters."""
        with pytest.raises(ValidationError):
            ConfigRef(id=uuid4(), revision=1, hash="abc123")
    
    def test_catalog_ref(self):
        """CatalogRef wraps config ref with catalog key."""
        config_ref = ConfigRef(id=uuid4(), revision=1, hash="a" * 64)
        catalog_ref = CatalogRef(config_ref=config_ref, catalog_key="REASON_CODES")
        
        assert catalog_ref.config_ref == config_ref
        assert catalog_ref.catalog_key == "REASON_CODES"
    
    def test_reason_with_catalog(self):
        """Reason references catalog."""
        config_ref = ConfigRef(id=uuid4(), revision=1, hash="b" * 64)
        catalog_ref = CatalogRef(config_ref=config_ref, catalog_key="DISMISS_REASONS")
        reason = Reason(code="NOT_RELEVANT", catalog_ref=catalog_ref)
        
        assert reason.code == "NOT_RELEVANT"
        assert reason.catalog_ref.catalog_key == "DISMISS_REASONS"
    
    def test_reason_with_other_text(self):
        """Reason with 'other' requires other_text."""
        config_ref = ConfigRef(id=uuid4(), revision=1, hash="c" * 64)
        catalog_ref = CatalogRef(config_ref=config_ref, catalog_key="REASONS")
        reason = Reason(
            code="OTHER",
            catalog_ref=catalog_ref,
            other_text="Custom explanation",
        )
        
        assert reason.code == "OTHER"
        assert reason.other_text == "Custom explanation"


class TestCommonScalars:
    """Test common scalar types."""
    
    def test_money_valid(self):
        """Money with finite decimal amount."""
        money = Money(amount=Decimal("12345.67"), currency="USD")
        assert money.amount == Decimal("12345.67")
        assert money.currency == "USD"
    
    def test_money_rejects_infinite(self):
        """Money amount must be finite."""
        with pytest.raises(ValidationError):
            Money(amount=Decimal("Infinity"), currency="USD")
    
    def test_money_currency_3_chars(self):
        """Currency must be 3 characters."""
        with pytest.raises(ValidationError):
            Money(amount=Decimal("100"), currency="US")
    
    def test_field_value_text(self):
        """FieldValue with text type."""
        fv = FieldValue(type=FieldValueType.TEXT, value="some text")
        assert fv.type == FieldValueType.TEXT
        assert fv.value == "some text"
    
    def test_field_value_decimal(self):
        """FieldValue with decimal type."""
        fv = FieldValue(type=FieldValueType.DECIMAL, value=Decimal("123.45"))
        assert fv.type == FieldValueType.DECIMAL
        assert fv.value == Decimal("123.45")
    
    def test_field_value_choice_list(self):
        """FieldValue with choice list."""
        fv = FieldValue(type=FieldValueType.CHOICE_LIST, value=["option1", "option2"])
        assert fv.type == FieldValueType.CHOICE_LIST
        assert fv.value == ["option1", "option2"]
    
    def test_mapped_value(self):
        """MappedValue with catalog reference."""
        config_ref = ConfigRef(id=uuid4(), revision=1, hash="d" * 64)
        catalog_ref = CatalogRef(config_ref=config_ref, catalog_key="FIELDS")
        
        mapped = MappedValue(
            field_key="risk_tolerance",
            value=FieldValue(type=FieldValueType.CHOICE, value="MODERATE"),
            catalog_ref=catalog_ref,
        )
        
        assert mapped.field_key == "risk_tolerance"
        assert mapped.value.type == FieldValueType.CHOICE


class TestArtifactReferences:
    """Test artifact and item references."""
    
    def test_artifact_ref(self):
        """ArtifactRef with stable IDs and hash."""
        artifact_id = uuid4()
        revision_id = uuid4()
        
        ref = ArtifactRef(
            artifact_id=artifact_id,
            revision_id=revision_id,
            version=1,
            hash="e" * 64,
        )
        
        assert ref.artifact_id == artifact_id
        assert ref.revision_id == revision_id
        assert ref.version == 1
        assert ref.hash == "e" * 64
    
    def test_evidence_ref(self):
        """EvidenceRef points to source."""
        source_id = uuid4()
        ref = EvidenceRef(source_id=source_id, source_version="v2")
        
        assert ref.source_id == source_id
        assert ref.source_version == "v2"
    
    def test_item_ref(self):
        """ItemRef combines artifact ref with item key/hash."""
        artifact_id = uuid4()
        revision_id = uuid4()
        
        item_ref = ItemRef(
            artifact_ref=ArtifactRef(
                artifact_id=artifact_id,
                revision_id=revision_id,
                version=1,
                hash="f" * 64,
            ),
            item_key="section_portfolio_overview",
            item_hash="1" * 64,
        )
        
        assert item_ref.artifact_ref.artifact_id == artifact_id
        assert item_ref.item_key == "section_portfolio_overview"
        assert item_ref.item_hash == "1" * 64


class TestReviewTypes:
    """Test review decision types."""
    
    def test_review_item_scope(self):
        """Review with item scope."""
        review = Review(
            id=uuid4(),
            scope=ReviewScope.ITEM,
            item_key="section_1",
            item_hash="g" * 64,
            decision=ReviewDecision.APPROVED,
            actor="rm001@example.com",
            at=datetime.now(timezone.utc),
        )
        
        assert review.scope == ReviewScope.ITEM
        assert review.item_key == "section_1"
        assert review.decision == ReviewDecision.APPROVED
    
    def test_review_artifact_scope(self):
        """Review with artifact scope."""
        review = Review(
            id=uuid4(),
            scope=ReviewScope.ARTIFACT,
            item_key=None,
            item_hash="a" * 64,
            decision=ReviewDecision.REJECTED,
            actor="rm002@example.com",
            at=datetime.now(timezone.utc),
            reason=Reason(
                code="UNSUPPORTED_FACT",
                catalog_ref=CatalogRef(
                    config_ref=ConfigRef(id=uuid4(), revision=1, hash="b" * 64),
                    catalog_key="REJECTION_REASONS",
                ),
            ),
        )
        
        assert review.scope == ReviewScope.ARTIFACT
        assert review.item_key is None
        assert review.decision == ReviewDecision.REJECTED
        assert review.reason is not None
    
    def test_review_item(self):
        """ReviewItem with state and evidence."""
        item = ReviewItem(
            key="section_market_news",
            hash="j" * 64,
            review_state=ReviewState.APPROVED,
            evidence_refs=[
                EvidenceRef(source_id=uuid4(), source_version="v1"),
            ],
        )
        
        assert item.key == "section_market_news"
        assert item.review_state == ReviewState.APPROVED
        assert len(item.evidence_refs) == 1


class TestBlockersAndCapability:
    """Test blocker and capability state."""
    
    def test_blocker_with_config_ref(self):
        """Blocker references missing config."""
        blocker = Blocker(
            code="MISSING_POLICY",
            field="consent_policy_ref",
            config_ref=ConfigRef(id=uuid4(), revision=1, hash="c" * 64),
            resolution=BlockerResolution.ADMIN,
        )
        
        assert blocker.code == "MISSING_POLICY"
        assert blocker.resolution == BlockerResolution.ADMIN
    
    def test_blocker_without_config(self):
        """Blocker without config reference."""
        blocker = Blocker(
            code="VALIDATION_ERROR",
            field="email",
            resolution=BlockerResolution.EDIT,
        )
        
        assert blocker.code == "VALIDATION_ERROR"
        assert blocker.config_ref is None
    
    def test_capability_ready(self):
        """Capability in ready state."""
        cap = Capability(
            key="brief.generate",
            state=CapabilityState.READY,
            blockers=[],
        )
        
        assert cap.key == "brief.generate"
        assert cap.state == CapabilityState.READY
        assert len(cap.blockers) == 0
    
    def test_capability_unconfigured_with_blockers(self):
        """Capability unconfigured with blockers."""
        cap = Capability(
            key="capture.start",
            state=CapabilityState.UNCONFIGURED,
            blockers=[
                Blocker(
                    code="MISSING_CONSENT_POLICY",
                    resolution=BlockerResolution.ADMIN,
                ),
            ],
        )
        
        assert cap.state == CapabilityState.UNCONFIGURED
        assert len(cap.blockers) == 1
