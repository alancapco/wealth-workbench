"""Shariah evidence service - fetch and validate evidence from certified bodies.

U-015: Evidence-backed Shariah compliance (default OFF, DEC-05 gated).
"""
from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.shariah import EvidenceRepository
from app.services.shariah.rag_service import ShariahRagService


class EvidenceService:
    """Service for managing Shariah compliance evidence.
    
    Handles evidence from certified bodies (AAOIFI, SSB screening reports).
    Returns UNCONFIGURED without DEC-05 gate and certified provider.
    Provider is "configured" when aaoifi_clauses with approval_status='approved' exist.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)

    async def _rag_provider_configured(self) -> bool:
        """Return True if the local AAOIFI knowledge base has been ingested and approved."""
        if not settings.database_configured:
            return False
        try:
            rag = ShariahRagService(db_url=settings.DATABASE_URL)  # type: ignore[arg-type]
            result = await rag.has_approved_clauses()
            await rag.close()
            return result
        except Exception:
            return False

    async def fetch_evidence(
        self,
        tenant_id: str,
        product_ref: str,
        dec_05_enabled: bool = False,
        provider_configured: bool = False,
    ) -> dict:
        """Fetch evidence for product.
        
        Returns UNCONFIGURED if DEC-05 OFF or no certified provider.
        provider_configured is overridden by checking the local AAOIFI knowledge base.
        
        Args:
            tenant_id: Tenant identifier
            product_ref: Product reference
            dec_05_enabled: DEC-05 Shariah pilot gate status (legacy param, checked from settings)
            provider_configured: Legacy param; actual check uses AAOIFI knowledge base rows
            
        Returns:
            Evidence data or UNCONFIGURED status
        """
        dec_05_active = dec_05_enabled or settings.SHARIAH_DEC05_ENABLED
        rag_ready = await self._rag_provider_configured()

        # DEC-05 gate: feature OFF blocks evidence fetch
        if not dec_05_active or not rag_ready:
            message = (
                "Shariah pilot requires DEC-05 gate and certified provider"
                if not dec_05_active
                else "AAOIFI knowledge base not yet ingested. Run: python -m app.scripts.ingest_aaoifi"
            )
            return {
                "status": "UNCONFIGURED",
                "message": message,
            }

        # Fetch evidence from repository
        evidence_list = await self.evidence_repo.get_by_product(tenant_id, product_ref)

        return {
            "status": "SUCCESS",
            "evidence_count": len(evidence_list),
            "evidence": [
                {
                    "id": str(ev.id),
                    "evidence_type": ev.evidence_type,
                    "source_url": ev.source_url,
                    "captured_at": ev.captured_at.isoformat(),
                    "expires_at": ev.expires_at.isoformat() if ev.expires_at else None,
                    "certification_body": ev.certification_body,
                    "compliance_status": ev.compliance_status,
                }
                for ev in evidence_list
            ],
        }

    async def validate_evidence_freshness(
        self, tenant_id: str, evidence_id: UUID, as_of: datetime
    ) -> bool:
        """Check if evidence is still valid (not expired).
        
        Args:
            tenant_id: Tenant identifier
            evidence_id: Evidence UUID
            as_of: Time to check validity
            
        Returns:
            True if evidence is current, False if expired
        """
        evidence = await self.evidence_repo.get_by_id(tenant_id, evidence_id)
        if not evidence:
            return False

        # No expiry = always valid
        if evidence.expires_at is None:
            return True

        # Check expiry
        return evidence.expires_at > as_of

    def cite_sources(self, evidence_list: list) -> list[dict]:
        """Format evidence citations for UI display.
        
        Args:
            evidence_list: List of ShariahEvidence objects
            
        Returns:
            Formatted citations with source, body, and URL
        """
        citations = []
        for ev in evidence_list:
            citations.append({
                "evidence_id": str(ev.id),
                "source_type": ev.evidence_type,
                "certification_body": ev.certification_body,
                "source_url": ev.source_url,
                "captured_at": ev.captured_at.isoformat(),
                "status": ev.compliance_status,
            })
        return citations
