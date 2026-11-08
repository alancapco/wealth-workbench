"""Shariah estimate service - generate compliance estimates with disclaimers.

U-015: Preliminary technical estimate, NOT fatwa or religious authority ruling.
When DEC-05 is enabled, calls ShariahComplianceService for AAOIFI-backed analysis.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.shariah import EstimateRepository, EvidenceRepository


# Explicit disclaimer per U-015 architecture requirement
ESTIMATE_DISCLAIMER = (
    "This is a preliminary technical estimate based on available evidence. "
    "It is NOT a fatwa, religious authority ruling, or compliance approval. "
    "Consult qualified Shariah scholars before making investment decisions."
)


class EstimateService:
    """Service for generating Shariah compliance estimates.
    
    Generates preliminary estimates based on evidence from certified bodies.
    Always includes explicit disclaimer that this is not authoritative ruling.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.estimate_repo = EstimateRepository(db)

    async def generate_estimate(
        self,
        tenant_id: str,
        product_ref: str,
        workflow_id: UUID,
        product_description: str = "",
    ) -> dict:
        """Generate Shariah compliance estimate for product.
        
        When DEC-05 is enabled (settings.SHARIAH_DEC05_ENABLED), delegates to
        ShariahComplianceService for AAOIFI RAG-backed analysis.

        Legacy logic per U-015 (DEC-05 OFF):
        - LIKELY_COMPLIANT: all evidence is COMPLIANT and current (not expired)
        - INSUFFICIENT_DATA: no evidence or all evidence expired
        - LIKELY_NON_COMPLIANT: any evidence is NON_COMPLIANT
        
        Always includes limitations disclaimer.
        
        Args:
            tenant_id: Tenant identifier
            product_ref: Product reference
            workflow_id: Workflow context
            product_description: Optional product description for RAG analysis
            
        Returns:
            Estimate with evidence, reasoning, and disclaimer
        """
        # DEC-05 path: use AAOIFI RAG-backed compliance estimation
        if settings.SHARIAH_DEC05_ENABLED:
            from app.services.shariah.compliance_service import ShariahComplianceService
            svc = ShariahComplianceService()
            description = product_description or product_ref
            rag_result = await svc.estimate_compliance(
                product_ref=product_ref,
                product_description=description,
                workflow_id=str(workflow_id),
            )

            # Map RAG findings to evidence-layer estimate and persist
            findings = rag_result.get("findings", [])
            has_critical = any(f.get("severity") == "critical" for f in findings)
            estimate_value = rag_result["estimate"]
            reasoning = (
                f"AAOIFI RAG analysis: {len(findings)} finding(s) identified. "
                + (" Critical concerns detected." if has_critical else "")
                + f" Confidence: {rag_result.get('confidence', 'medium')}."
            )

            estimate_id = uuid4()
            estimate = await self.estimate_repo.create_estimate(
                estimate_id=estimate_id,
                tenant_id=tenant_id,
                product_ref=product_ref,
                workflow_id=workflow_id,
                estimate=estimate_value,
                evidence_ids=[],
                reasoning=reasoning,
                limitations=rag_result["disclaimer"],
            )
            return {
                "estimate_id": str(estimate.id),
                "product_ref": product_ref,
                "estimate": estimate_value,
                "reasoning": reasoning,
                "evidence_count": 0,
                "evidence_ids": [],
                "disclaimer": rag_result["disclaimer"],
                "created_at": estimate.created_at.isoformat(),
                "rag_findings": findings,
                "candidate_sources": rag_result.get("candidate_sources", []),
                "model_used": rag_result.get("model_used", ""),
            }

        now = datetime.now(UTC)

        # Fetch valid (non-expired) evidence
        valid_evidence = await self.evidence_repo.list_valid_evidence(
            tenant_id, product_ref, now
        )

        # No evidence or all expired → INSUFFICIENT_DATA
        if not valid_evidence:
            estimate_value = "INSUFFICIENT_DATA"
            reasoning = (
                "No current evidence available from certified bodies. "
                "Evidence may be missing or expired."
            )
            evidence_ids = []

        # Check for any NON_COMPLIANT evidence
        elif any(ev.compliance_status == "NON_COMPLIANT" for ev in valid_evidence):
            estimate_value = "LIKELY_NON_COMPLIANT"
            reasoning = (
                "At least one certified source indicates non-compliance. "
                "This preliminary estimate suggests the product may not meet "
                "Shariah compliance criteria based on available evidence."
            )
            evidence_ids = [ev.id for ev in valid_evidence]

        # All evidence is COMPLIANT → LIKELY_COMPLIANT
        elif all(ev.compliance_status == "COMPLIANT" for ev in valid_evidence):
            estimate_value = "LIKELY_COMPLIANT"
            reasoning = (
                f"All {len(valid_evidence)} current evidence source(s) from certified "
                "bodies indicate compliance. This preliminary estimate suggests the "
                "product may meet Shariah compliance criteria based on available evidence."
            )
            evidence_ids = [ev.id for ev in valid_evidence]

        # Mixed or UNCERTAIN evidence
        else:
            estimate_value = "INSUFFICIENT_DATA"
            reasoning = (
                "Evidence sources provide uncertain or mixed signals. "
                "Additional review by qualified Shariah scholars is required."
            )
            evidence_ids = [ev.id for ev in valid_evidence]

        # Create estimate record
        estimate_id = uuid4()
        estimate = await self.estimate_repo.create_estimate(
            estimate_id=estimate_id,
            tenant_id=tenant_id,
            product_ref=product_ref,
            workflow_id=workflow_id,
            estimate=estimate_value,
            evidence_ids=evidence_ids,
            reasoning=reasoning,
            limitations=ESTIMATE_DISCLAIMER,
        )

        return {
            "estimate_id": str(estimate.id),
            "product_ref": product_ref,
            "estimate": estimate_value,
            "reasoning": reasoning,
            "evidence_count": len(evidence_ids),
            "evidence_ids": [str(eid) for eid in evidence_ids],
            "disclaimer": ESTIMATE_DISCLAIMER,
            "created_at": estimate.created_at.isoformat(),
        }

    async def get_estimate(
        self, tenant_id: str, estimate_id: UUID
    ) -> dict | None:
        """Retrieve existing estimate by ID.
        
        Args:
            tenant_id: Tenant identifier
            estimate_id: Estimate UUID
            
        Returns:
            Estimate data with disclaimer, or None if not found
        """
        estimate = await self.estimate_repo.get_by_id(tenant_id, estimate_id)
        if not estimate:
            return None

        return {
            "estimate_id": str(estimate.id),
            "product_ref": estimate.product_ref,
            "workflow_id": str(estimate.workflow_id),
            "estimate": estimate.estimate,
            "reasoning": estimate.reasoning,
            "evidence_ids": [str(eid) for eid in estimate.evidence_ids],
            "disclaimer": estimate.limitations,
            "created_at": estimate.created_at.isoformat(),
        }

    async def list_by_workflow(
        self, tenant_id: str, workflow_id: UUID
    ) -> list[dict]:
        """List all estimates for a workflow.
        
        Args:
            tenant_id: Tenant identifier
            workflow_id: Workflow UUID
            
        Returns:
            List of estimates with disclaimers
        """
        estimates = await self.estimate_repo.list_by_workflow(tenant_id, workflow_id)

        return [
            {
                "estimate_id": str(est.id),
                "product_ref": est.product_ref,
                "estimate": est.estimate,
                "reasoning": est.reasoning,
                "evidence_count": len(est.evidence_ids),
                "created_at": est.created_at.isoformat(),
            }
            for est in estimates
        ]
