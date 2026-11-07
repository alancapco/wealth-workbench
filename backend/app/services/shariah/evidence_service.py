"""Shariah evidence service - fetch and validate evidence from certified bodies.

U-015: Evidence-backed Shariah compliance (default OFF, DEC-05 gated).
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.shariah import EvidenceRepository


class EvidenceService:
    """Service for managing Shariah compliance evidence.
    
    Handles evidence from certified bodies (AAOIFI, SSB screening reports).
    Returns UNCONFIGURED without DEC-05 gate and certified provider.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)

    async def fetch_evidence(
        self,
        tenant_id: str,
        product_ref: str,
        dec_05_enabled: bool = False,
        provider_configured: bool = False,
    ) -> dict:
        """Fetch evidence for product.
        
        Returns UNCONFIGURED if DEC-05 OFF or no certified provider.
        
        Args:
            tenant_id: Tenant identifier
            product_ref: Product reference
            dec_05_enabled: DEC-05 Shariah pilot gate status
            provider_configured: Whether certified provider is configured
            
        Returns:
            Evidence data or UNCONFIGURED status
        """
        # DEC-05 gate: feature OFF blocks evidence fetch
        if not dec_05_enabled or not provider_configured:
            return {
                "status": "UNCONFIGURED",
                "message": "Shariah pilot requires DEC-05 gate and certified provider",
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
