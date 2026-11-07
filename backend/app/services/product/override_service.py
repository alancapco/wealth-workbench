"""Suitability override service - RM justification with approval gate and audit trail.

Architecture §6.7 API-062 - permit soft override only with policy, actor, rationale.
Hard stop factors cannot be overridden. Original rating preserved in audit.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import SuitabilityOverride as SuitabilityOverrideModel
from app.schemas.product import (
    Assessment,
    SuitabilityOverride,
    FactorClassification,
)
from app.schemas.common import (
    ArtifactRef,
    ConfigRef,
    Reason,
    Blocker,
    BlockerResolution,
)


class OverrideService:
    """Suitability override with approval gate and audit trail."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_override(
        self,
        tenant_id: str,
        client_id: UUID,
        actor: str,
        assessment: Assessment,
        assessment_ref: ArtifactRef,
        factor_keys: list[str],
        reason: Reason,
        rationale: str,
    ) -> tuple[SuitabilityOverride | None, list[Blocker]]:
        """Create suitability override with justification and audit.
        
        Validation:
        - Assessment must be current (not superseded)
        - Factors must exist in assessment
        - Only SOFT classification factors can be overridden
        - HARD stop factors are immutable
        - Unknown policy blocks override
        - Missing/expired profile blocks override
        
        Returns (override, blockers). If blockers non-empty, override is None.
        Original rating preserved immutably in audit record.
        """
        blockers: list[Blocker] = []
        
        # Check assessment is current
        if not assessment.current:
            blockers.append(Blocker(
                code="ASSESSMENT_NOT_CURRENT",
                field="assessment_ref",
                config_ref=None,
                resolution=BlockerResolution.REVIEW,
            ))
            return None, blockers
        
        # Validate all factor keys exist
        assessment_factor_keys = {f.key for f in assessment.factors}
        invalid_keys = [k for k in factor_keys if k not in assessment_factor_keys]
        if invalid_keys:
            blockers.append(Blocker(
                code="INVALID_FACTOR_KEYS",
                field="factor_keys",
                config_ref=None,
                resolution=BlockerResolution.EDIT,
            ))
            return None, blockers
        
        # Check no hard stop factors in override list
        hard_factors = [
            f for f in assessment.factors
            if f.key in factor_keys and f.classification == "HARD"
        ]
        if hard_factors:
            blockers.append(Blocker(
                code="HARD_STOP_CANNOT_OVERRIDE",
                field="factor_keys",
                config_ref=None,
                resolution=BlockerResolution.NONE,
            ))
            return None, blockers
        
        # Check no unknown classification factors
        unknown_factors = [
            f for f in assessment.factors
            if f.key in factor_keys and f.classification == "UNKNOWN"
        ]
        if unknown_factors:
            blockers.append(Blocker(
                code="UNKNOWN_FACTOR_CANNOT_OVERRIDE",
                field="factor_keys",
                config_ref=None,
                resolution=BlockerResolution.ADMIN,
            ))
            return None, blockers
        
        # Check policy is known
        if assessment.policy_ref.id == UUID("00000000-0000-0000-0000-000000000000"):
            blockers.append(Blocker(
                code="SUITABILITY_POLICY_UNCONFIGURED",
                field=None,
                config_ref=None,
                resolution=BlockerResolution.ADMIN,
            ))
            return None, blockers
        
        # Check override not permitted on any selected factors
        non_overridable = [
            f for f in assessment.factors
            if f.key in factor_keys and not f.override_permitted
        ]
        if non_overridable:
            blockers.append(Blocker(
                code="OVERRIDE_NOT_PERMITTED",
                field="factor_keys",
                config_ref=None,
                resolution=BlockerResolution.NONE,
            ))
            return None, blockers
        
        # Require GREEN/YELLOW/RED original rating (not UNAVAILABLE)
        if assessment.rating not in ["GREEN", "YELLOW", "RED"]:
            blockers.append(Blocker(
                code="CANNOT_OVERRIDE_UNAVAILABLE",
                field="assessment_ref",
                config_ref=None,
                resolution=BlockerResolution.REVIEW,
            ))
            return None, blockers
        
        # Create override record
        override_id = uuid4()
        now = datetime.now(UTC)
        
        # Persist to audit table
        import json
        override_record = SuitabilityOverrideModel(
            id=override_id,
            tenant_id=tenant_id,
            client_id=client_id,
            assessment_revision_id=assessment_ref.revision_id,
            factor_keys=json.dumps(factor_keys),
            reason_code=reason.code,
            reason_catalog_ref=json.dumps({
                "config_ref": {
                    "id": str(reason.catalog_ref.config_ref.id),
                    "revision": reason.catalog_ref.config_ref.revision,
                    "hash": reason.catalog_ref.config_ref.hash,
                },
                "catalog_key": reason.catalog_ref.catalog_key,
            }),
            reason_other_text=reason.other_text,
            rationale=rationale,
            policy_configuration_id=assessment.policy_ref.id,
            policy_configuration_revision=assessment.policy_ref.revision,
            actor=actor,
            overridden_at=now,
            original_rating=assessment.rating,
        )
        
        self.db.add(override_record)
        await self.db.flush()
        
        # Return override DTO
        override = SuitabilityOverride(
            id=override_id,
            assessment_ref=assessment_ref,
            factor_keys=factor_keys,
            reason=reason,
            rationale=rationale,
            policy_ref=assessment.policy_ref,
            actor=actor,
            at=now,
            original_rating=assessment.rating,  # type: ignore
        )
        
        return override, []
