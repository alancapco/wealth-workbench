"""Suitability assessment service - automated match, conflict detection, explainability.

Architecture §6.7 API-061 - assess product suitability against current profile.
Pre-screen only, not compliance approval. Missing/expired profile blocks GREEN rating.
"""
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

from app.schemas.product import (
    Assessment,
    ProductRef,
    ProfileValidity,
    SuitabilityRating,
    SuitabilityFactor,
    FactorClassification,
    FactorResult,
)
from app.schemas.common import (
    ArtifactRef,
    ConfigRef,
    EvidenceRef,
    Blocker,
    BlockerResolution,
    Hash,
    Money,
)


class SuitabilityService:
    """Suitability assessment - automated conflict detection with explainability."""
    
    def __init__(self, policy_ref: ConfigRef | None):
        self.policy_ref = policy_ref
    
    async def assess_suitability(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
        account_ref: str | None,
        amount: Money | None,
    ) -> Assessment:
        """Assess product suitability against current client profile.
        
        Returns:
            GREEN - no detected conflict (not compliance approval)
            YELLOW - review required
            RED - conflict or prohibition
            UNAVAILABLE - unknown policy or profile unavailable
        
        Missing/expired/conflict profile cannot yield GREEN.
        Hard stop factors cannot be overridden.
        Soft factors permit override with justification.
        """
        # Check profile availability (stub - real impl queries profile service)
        profile_validity = await self._check_profile_validity(tenant_id, client_id)
        
        # UNAVAILABLE: no approved suitability policy configured
        if self.policy_ref is None:
            return Assessment(
                client_id=client_id,
                product_ref=product_ref,
                account_ref=account_ref,
                amount=amount,
                profile_id=None,
                profile_version=None,
                profile_validity=profile_validity,
                input_hash=self._compute_input_hash(client_id, product_ref, account_ref, amount),
                policy_ref=ConfigRef(
                    id=uuid4(),
                    revision=1,
                    hash="0" * 64,
                ),
                rating="UNAVAILABLE",
                current=True,
                factors=[],
                ticket_eligible=False,
                blockers=[
                    Blocker(
                        code="SUITABILITY_POLICY_UNCONFIGURED",
                        field=None,
                        config_ref=None,
                        resolution=BlockerResolution.ADMIN,
                    )
                ],
                assessed_at=datetime.utcnow(),
            )
        
        # Missing/expired profile blocks GREEN and ticket
        if profile_validity in ["MISSING", "EXPIRED", "CONFLICT"]:
            return Assessment(
                client_id=client_id,
                product_ref=product_ref,
                account_ref=account_ref,
                amount=amount,
                profile_id=None,
                profile_version=None,
                profile_validity=profile_validity,
                input_hash=self._compute_input_hash(client_id, product_ref, account_ref, amount),
                policy_ref=self.policy_ref,
                rating="RED",
                current=True,
                factors=[
                    SuitabilityFactor(
                        key="profile_validity",
                        label="Current KYC/Profile Required",
                        classification="HARD",
                        result="FAIL",
                        evidence_refs=[],
                        explanation=f"Profile status: {profile_validity}. Current suitability data required.",
                        override_permitted=False,
                    )
                ],
                ticket_eligible=False,
                blockers=[
                    Blocker(
                        code="PROFILE_MISSING_OR_EXPIRED",
                        field="profile",
                        config_ref=None,
                        resolution=BlockerResolution.ADMIN,
                    )
                ],
                assessed_at=datetime.utcnow(),
            )
        
        # Evaluate factors (stub - real impl queries profile and product risk/objective match)
        factors = await self._evaluate_factors(
            tenant_id,
            client_id,
            product_ref,
            account_ref,
            amount,
        )
        
        # Determine rating from factor results
        rating = self._compute_rating(factors)
        
        # Ticket eligible only if not RED and profile current
        ticket_eligible = rating != "RED" and profile_validity == "CURRENT"
        
        blockers = []
        if not ticket_eligible:
            blockers.append(
                Blocker(
                    code="TICKET_NOT_ELIGIBLE",
                    field=None,
                    config_ref=None,
                    resolution=BlockerResolution.REVIEW if rating == "YELLOW" else BlockerResolution.ADMIN,
                )
            )
        
        return Assessment(
            client_id=client_id,
            product_ref=product_ref,
            account_ref=account_ref,
            amount=amount,
            profile_id="profile_001" if profile_validity == "CURRENT" else None,
            profile_version="v1" if profile_validity == "CURRENT" else None,
            profile_validity=profile_validity,
            input_hash=self._compute_input_hash(client_id, product_ref, account_ref, amount),
            policy_ref=self.policy_ref,
            rating=rating,
            current=True,
            factors=factors,
            ticket_eligible=ticket_eligible,
            blockers=blockers,
            assessed_at=datetime.utcnow(),
        )
    
    async def _check_profile_validity(
        self,
        tenant_id: str,
        client_id: UUID,
    ) -> ProfileValidity:
        """Check current profile status (stub)."""
        # Real implementation queries profile service for KYC freshness
        # Returns CURRENT if profile exists and not expired
        return "CURRENT"
    
    async def _evaluate_factors(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
        account_ref: str | None,
        amount: Money | None,
    ) -> list[SuitabilityFactor]:
        """Evaluate suitability factors (stub - real impl matches profile to product)."""
        # Real implementation would:
        # 1. Query client risk profile and investment objectives
        # 2. Query product risk rating and characteristics
        # 3. Check concentration limits if amount provided
        # 4. Verify account type compatibility
        # 5. Check regulatory restrictions per jurisdiction
        
        # Stub: return sample factors
        return [
            SuitabilityFactor(
                key="risk_match",
                label="Risk Profile Match",
                classification="SOFT",
                result="PASS",
                evidence_refs=[],
                explanation="Product risk aligns with client risk tolerance.",
                override_permitted=True,
            ),
            SuitabilityFactor(
                key="objective_match",
                label="Investment Objective Match",
                classification="SOFT",
                result="PASS",
                evidence_refs=[],
                explanation="Product objectives consistent with client goals.",
                override_permitted=True,
            ),
        ]
    
    def _compute_rating(self, factors: list[SuitabilityFactor]) -> SuitabilityRating:
        """Compute overall rating from factor results."""
        # Any hard FAIL -> RED (cannot override)
        for factor in factors:
            if factor.classification == "HARD" and factor.result == "FAIL":
                return "RED"
        
        # Any FAIL or WARN -> YELLOW (review required)
        for factor in factors:
            if factor.result in ["FAIL", "WARN"]:
                return "YELLOW"
        
        # Any MISSING -> YELLOW
        for factor in factors:
            if factor.result == "MISSING":
                return "YELLOW"
        
        # All PASS -> GREEN (no detected conflict, not compliance approval)
        return "GREEN"
    
    def _compute_input_hash(
        self,
        client_id: UUID,
        product_ref: ProductRef,
        account_ref: str | None,
        amount: Money | None,
    ) -> str:
        """Compute hash of assessment inputs."""
        # Stub: real implementation hashes client_id, product_ref, account, amount
        import hashlib
        amount_str = f"{amount.amount}:{amount.currency}" if amount else "null"
        data = f"{client_id}:{product_ref.id}:{product_ref.version}:{account_ref}:{amount_str}"
        return hashlib.sha256(data.encode()).hexdigest()
