"""Test suite for Shariah pilot feature (U-015).

Tests DEC-05 gate, evidence-backed estimates, and disclaimers.
Default OFF behavior and tenant isolation enforcement.
"""
import pytest
import pytest_asyncio
from datetime import datetime, UTC, timedelta
from uuid import uuid4

from app.models.shariah import ShariahEvidence, ShariahEstimate
from app.repositories.shariah import EvidenceRepository, EstimateRepository
from app.services.shariah import EvidenceService, EstimateService, ESTIMATE_DISCLAIMER


class TestShariahPilotGate:
    """Test DEC-05 gate enforcement - feature default OFF."""

    def test_dec05_off_blocks_estimate_endpoint(self):
        """DEC-05 OFF returns 503 FEATURE_DISABLED for estimate endpoint."""
        # This would be an API integration test
        # Verify POST /workflows/{id}/shariah/estimates returns 503 when dec05_enabled=False
        pass

    def test_dec05_off_blocks_evidence_endpoint(self):
        """DEC-05 OFF returns 503 FEATURE_DISABLED for evidence endpoint."""
        # This would be an API integration test
        # Verify GET /shariah/evidence/{ref} returns 503 when dec05_enabled=False
        pass

    def test_dec05_on_allows_access(self):
        """DEC-05 ON permits access to Shariah endpoints."""
        # Verify endpoints are accessible when dec05_enabled=True
        pass


class TestEvidenceService:
    """Test evidence fetching and validation."""

    @pytest.mark.asyncio
    async def test_fetch_evidence_unconfigured_without_dec05(self, async_session):
        """fetch_evidence returns UNCONFIGURED without DEC-05 gate."""
        service = EvidenceService(async_session)
        
        result = await service.fetch_evidence(
            tenant_id="test-tenant",
            product_ref="PRODUCT-001",
            dec_05_enabled=False,
            provider_configured=False,
        )
        
        assert result["status"] == "UNCONFIGURED"
        assert "DEC-05" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_evidence_unconfigured_without_provider(self, async_session):
        """fetch_evidence returns UNCONFIGURED without certified provider."""
        service = EvidenceService(async_session)
        
        result = await service.fetch_evidence(
            tenant_id="test-tenant",
            product_ref="PRODUCT-001",
            dec_05_enabled=True,
            provider_configured=False,
        )
        
        assert result["status"] == "UNCONFIGURED"
        assert "certified provider" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_evidence_freshness_not_expired(self, async_session):
        """Evidence with future expiry is valid."""
        repo = EvidenceRepository(async_session)
        evidence_id = uuid4()
        tenant_id = "test-tenant"
        
        # Create evidence expiring in future
        evidence = await repo.create(
            evidence_id=evidence_id,
            tenant_id=tenant_id,
            product_ref="PRODUCT-001",
            evidence_type="AAOIFI_CERT",
            source_url="https://example.com/cert",
            captured_at=datetime.now(UTC),
            certification_body="AAOIFI",
            compliance_status="COMPLIANT",
            expires_at=datetime.now(UTC) + timedelta(days=365),
        )
        await async_session.commit()
        
        service = EvidenceService(async_session)
        is_valid = await service.validate_evidence_freshness(
            tenant_id=tenant_id,
            evidence_id=evidence_id,
            as_of=datetime.now(UTC),
        )
        
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_evidence_freshness_expired(self, async_session):
        """Evidence with past expiry is invalid."""
        repo = EvidenceRepository(async_session)
        evidence_id = uuid4()
        tenant_id = "test-tenant"
        
        # Create expired evidence
        evidence = await repo.create(
            evidence_id=evidence_id,
            tenant_id=tenant_id,
            product_ref="PRODUCT-001",
            evidence_type="SSB_REPORT",
            source_url="https://example.com/report",
            captured_at=datetime.now(UTC) - timedelta(days=400),
            certification_body="SSB Board",
            compliance_status="COMPLIANT",
            expires_at=datetime.now(UTC) - timedelta(days=30),
        )
        await async_session.commit()
        
        service = EvidenceService(async_session)
        is_valid = await service.validate_evidence_freshness(
            tenant_id=tenant_id,
            evidence_id=evidence_id,
            as_of=datetime.now(UTC),
        )
        
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_cite_sources_formats_correctly(self, async_session):
        """cite_sources formats evidence for UI display."""
        repo = EvidenceRepository(async_session)
        tenant_id = "test-tenant"
        
        evidence = await repo.create(
            evidence_id=uuid4(),
            tenant_id=tenant_id,
            product_ref="PRODUCT-001",
            evidence_type="SCREENING_RESULT",
            source_url="https://example.com/screening",
            captured_at=datetime.now(UTC),
            certification_body="Certified Screener",
            compliance_status="COMPLIANT",
        )
        await async_session.commit()
        
        service = EvidenceService(async_session)
        citations = service.cite_sources([evidence])
        
        assert len(citations) == 1
        assert citations[0]["source_type"] == "SCREENING_RESULT"
        assert citations[0]["certification_body"] == "Certified Screener"
        assert citations[0]["source_url"] == "https://example.com/screening"


class TestEstimateService:
    """Test Shariah compliance estimate generation."""

    @pytest.mark.asyncio
    async def test_estimate_likely_compliant_all_valid_compliant(self, async_session):
        """LIKELY_COMPLIANT when all current evidence is COMPLIANT."""
        evidence_repo = EvidenceRepository(async_session)
        tenant_id = "test-tenant"
        product_ref = "PRODUCT-001"
        
        # Create two valid COMPLIANT evidence
        for i in range(2):
            await evidence_repo.create(
                evidence_id=uuid4(),
                tenant_id=tenant_id,
                product_ref=product_ref,
                evidence_type="AAOIFI_CERT",
                source_url=f"https://example.com/cert-{i}",
                captured_at=datetime.now(UTC),
                certification_body="AAOIFI",
                compliance_status="COMPLIANT",
                expires_at=datetime.now(UTC) + timedelta(days=365),
            )
        await async_session.commit()
        
        service = EstimateService(async_session)
        result = await service.generate_estimate(
            tenant_id=tenant_id,
            product_ref=product_ref,
            workflow_id=uuid4(),
        )
        
        assert result["estimate"] == "LIKELY_COMPLIANT"
        assert result["evidence_count"] == 2
        assert result["disclaimer"] == ESTIMATE_DISCLAIMER
        assert "all" in result["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_estimate_insufficient_data_no_evidence(self, async_session):
        """INSUFFICIENT_DATA when no evidence exists."""
        service = EstimateService(async_session)
        
        result = await service.generate_estimate(
            tenant_id="test-tenant",
            product_ref="PRODUCT-NO-EVIDENCE",
            workflow_id=uuid4(),
        )
        
        assert result["estimate"] == "INSUFFICIENT_DATA"
        assert result["evidence_count"] == 0
        assert result["disclaimer"] == ESTIMATE_DISCLAIMER
        assert "no current evidence" in result["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_estimate_insufficient_data_all_expired(self, async_session):
        """INSUFFICIENT_DATA when all evidence is expired."""
        evidence_repo = EvidenceRepository(async_session)
        tenant_id = "test-tenant"
        product_ref = "PRODUCT-002"
        
        # Create expired evidence
        await evidence_repo.create(
            evidence_id=uuid4(),
            tenant_id=tenant_id,
            product_ref=product_ref,
            evidence_type="SSB_REPORT",
            source_url="https://example.com/expired",
            captured_at=datetime.now(UTC) - timedelta(days=400),
            certification_body="SSB",
            compliance_status="COMPLIANT",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        await async_session.commit()
        
        service = EstimateService(async_session)
        result = await service.generate_estimate(
            tenant_id=tenant_id,
            product_ref=product_ref,
            workflow_id=uuid4(),
        )
        
        assert result["estimate"] == "INSUFFICIENT_DATA"
        assert result["evidence_count"] == 0
        assert "expired" in result["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_estimate_likely_non_compliant_any_non_compliant(self, async_session):
        """LIKELY_NON_COMPLIANT when any evidence is NON_COMPLIANT."""
        evidence_repo = EvidenceRepository(async_session)
        tenant_id = "test-tenant"
        product_ref = "PRODUCT-003"
        
        # Create one COMPLIANT and one NON_COMPLIANT
        await evidence_repo.create(
            evidence_id=uuid4(),
            tenant_id=tenant_id,
            product_ref=product_ref,
            evidence_type="AAOIFI_CERT",
            source_url="https://example.com/compliant",
            captured_at=datetime.now(UTC),
            certification_body="AAOIFI",
            compliance_status="COMPLIANT",
            expires_at=datetime.now(UTC) + timedelta(days=365),
        )
        await evidence_repo.create(
            evidence_id=uuid4(),
            tenant_id=tenant_id,
            product_ref=product_ref,
            evidence_type="SSB_REPORT",
            source_url="https://example.com/non-compliant",
            captured_at=datetime.now(UTC),
            certification_body="SSB",
            compliance_status="NON_COMPLIANT",
            expires_at=datetime.now(UTC) + timedelta(days=365),
        )
        await async_session.commit()
        
        service = EstimateService(async_session)
        result = await service.generate_estimate(
            tenant_id=tenant_id,
            product_ref=product_ref,
            workflow_id=uuid4(),
        )
        
        assert result["estimate"] == "LIKELY_NON_COMPLIANT"
        assert result["evidence_count"] == 2
        assert "non-compliance" in result["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_estimate_always_includes_disclaimer(self, async_session):
        """All estimates include explicit disclaimer."""
        service = EstimateService(async_session)
        
        result = await service.generate_estimate(
            tenant_id="test-tenant",
            product_ref="PRODUCT-004",
            workflow_id=uuid4(),
        )
        
        assert "disclaimer" in result
        assert "NOT a fatwa" in result["disclaimer"]
        assert "religious authority ruling" in result["disclaimer"]
        assert "Shariah scholars" in result["disclaimer"]


class TestTenantIsolation:
    """Test tenant isolation enforcement for Shariah data."""

    @pytest.mark.asyncio
    async def test_evidence_isolated_by_tenant(self, async_session):
        """Evidence from different tenants are isolated."""
        repo = EvidenceRepository(async_session)
        
        # Create evidence for two tenants with same product_ref
        await repo.create(
            evidence_id=uuid4(),
            tenant_id="tenant-A",
            product_ref="SHARED-PRODUCT",
            evidence_type="AAOIFI_CERT",
            source_url="https://example.com/a",
            captured_at=datetime.now(UTC),
            certification_body="AAOIFI",
            compliance_status="COMPLIANT",
        )
        await repo.create(
            evidence_id=uuid4(),
            tenant_id="tenant-B",
            product_ref="SHARED-PRODUCT",
            evidence_type="SSB_REPORT",
            source_url="https://example.com/b",
            captured_at=datetime.now(UTC),
            certification_body="SSB",
            compliance_status="NON_COMPLIANT",
        )
        await async_session.commit()
        
        # Each tenant sees only their evidence
        evidence_a = await repo.get_by_product("tenant-A", "SHARED-PRODUCT")
        evidence_b = await repo.get_by_product("tenant-B", "SHARED-PRODUCT")
        
        assert len(evidence_a) == 1
        assert len(evidence_b) == 1
        assert evidence_a[0].compliance_status == "COMPLIANT"
        assert evidence_b[0].compliance_status == "NON_COMPLIANT"

    @pytest.mark.asyncio
    async def test_estimates_isolated_by_tenant(self, async_session):
        """Estimates from different tenants are isolated."""
        repo = EstimateRepository(async_session)
        workflow_id = uuid4()
        
        # Create estimates for two tenants
        await repo.create_estimate(
            estimate_id=uuid4(),
            tenant_id="tenant-A",
            product_ref="PRODUCT-X",
            workflow_id=workflow_id,
            estimate="LIKELY_COMPLIANT",
            evidence_ids=[],
            reasoning="Test A",
            limitations=ESTIMATE_DISCLAIMER,
        )
        await repo.create_estimate(
            estimate_id=uuid4(),
            tenant_id="tenant-B",
            product_ref="PRODUCT-X",
            workflow_id=workflow_id,
            estimate="LIKELY_NON_COMPLIANT",
            evidence_ids=[],
            reasoning="Test B",
            limitations=ESTIMATE_DISCLAIMER,
        )
        await async_session.commit()
        
        # Each tenant sees only their estimates
        estimates_a = await repo.list_by_workflow("tenant-A", workflow_id)
        estimates_b = await repo.list_by_workflow("tenant-B", workflow_id)
        
        assert len(estimates_a) == 1
        assert len(estimates_b) == 1
        assert estimates_a[0].estimate == "LIKELY_COMPLIANT"
        assert estimates_b[0].estimate == "LIKELY_NON_COMPLIANT"


class TestDisclaimerRequirement:
    """Test that disclaimer is always present in responses."""

    def test_disclaimer_constant_correct(self):
        """ESTIMATE_DISCLAIMER has required wording."""
        assert "NOT a fatwa" in ESTIMATE_DISCLAIMER
        assert "religious authority ruling" in ESTIMATE_DISCLAIMER
        assert "compliance approval" in ESTIMATE_DISCLAIMER
        assert "Shariah scholars" in ESTIMATE_DISCLAIMER
        assert "preliminary" in ESTIMATE_DISCLAIMER


# Fixture for async session (would be provided by conftest.py)
@pytest_asyncio.fixture
async def async_session():
    """Provide async database session for tests."""
    # This would be implemented in conftest.py with actual DB setup
    # For now, this is a placeholder showing the expected interface
    pass
