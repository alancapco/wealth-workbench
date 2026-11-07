"""Shariah pilot repositories - tenant-scoped evidence and estimates.

U-015: Evidence-backed Shariah compliance estimation (default OFF).
"""
from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shariah import ShariahEstimate, ShariahEvidence
from app.repositories.base import TenantScopedRepository


class EvidenceRepository(TenantScopedRepository[ShariahEvidence]):
    """Repository for Shariah evidence with tenant isolation."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ShariahEvidence)

    async def create(
        self,
        evidence_id: UUID,
        tenant_id: str,
        product_ref: str,
        evidence_type: str,
        source_url: str,
        captured_at: datetime,
        certification_body: str,
        compliance_status: str,
        expires_at: datetime | None = None,
    ) -> ShariahEvidence:
        """Create new Shariah evidence record."""
        evidence = ShariahEvidence(
            id=evidence_id,
            tenant_id=tenant_id,
            product_ref=product_ref,
            evidence_type=evidence_type,
            source_url=source_url,
            captured_at=captured_at,
            expires_at=expires_at,
            certification_body=certification_body,
            compliance_status=compliance_status,
        )
        self.session.add(evidence)
        await self.session.flush()
        return evidence

    async def get_by_product(
        self, tenant_id: str, product_ref: str
    ) -> list[ShariahEvidence]:
        """Get all evidence for a product within tenant scope."""
        stmt = (
            select(ShariahEvidence)
            .where(
                ShariahEvidence.tenant_id == tenant_id,
                ShariahEvidence.product_ref == product_ref,
            )
            .order_by(ShariahEvidence.captured_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_valid_evidence(
        self, tenant_id: str, product_ref: str, as_of: datetime
    ) -> list[ShariahEvidence]:
        """List non-expired evidence for product at given time."""
        stmt = (
            select(ShariahEvidence)
            .where(
                ShariahEvidence.tenant_id == tenant_id,
                ShariahEvidence.product_ref == product_ref,
            )
            .where(
                # Evidence is valid if no expiry or not yet expired
                (ShariahEvidence.expires_at.is_(None))
                | (ShariahEvidence.expires_at > as_of)
            )
            .order_by(ShariahEvidence.captured_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class EstimateRepository(TenantScopedRepository[ShariahEstimate]):
    """Repository for Shariah estimates with tenant isolation."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ShariahEstimate)

    async def create_estimate(
        self,
        estimate_id: UUID,
        tenant_id: str,
        product_ref: str,
        workflow_id: UUID,
        estimate: str,
        evidence_ids: list[UUID],
        reasoning: str,
        limitations: str,
    ) -> ShariahEstimate:
        """Create new Shariah compliance estimate."""
        estimate_record = ShariahEstimate(
            id=estimate_id,
            tenant_id=tenant_id,
            product_ref=product_ref,
            workflow_id=workflow_id,
            estimate=estimate,
            evidence_ids=evidence_ids,
            reasoning=reasoning,
            limitations=limitations,
            created_at=datetime.now(UTC),
        )
        self.session.add(estimate_record)
        await self.session.flush()
        return estimate_record

    async def list_by_workflow(
        self, tenant_id: str, workflow_id: UUID
    ) -> list[ShariahEstimate]:
        """List all estimates for a workflow within tenant scope."""
        stmt = (
            select(ShariahEstimate)
            .where(
                ShariahEstimate.tenant_id == tenant_id,
                ShariahEstimate.workflow_id == workflow_id,
            )
            .order_by(ShariahEstimate.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
