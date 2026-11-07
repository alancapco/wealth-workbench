"""Shariah pilot API endpoints (default OFF, DEC-05 gated).

U-015: Evidence-backed Shariah compliance estimation.
API-075: POST /workflows/{workflow_id}/shariah/estimates - Generate estimate
API-076: GET /shariah/evidence/{product_ref} - List valid evidence

Feature is default OFF - returns 503 FEATURE_DISABLED if DEC-05 is OFF.
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import check_permission
from app.core.database import get_db
from app.core.identity import get_fixture_principal
from app.schemas.common import Envelope, ResponseMeta
from app.schemas.identity import Principal
from app.schemas.shariah import (
    ShariahEstimateRequest,
    ShariahEstimateResponse,
    ShariahEvidenceDetail,
    ShariahEvidenceListResponse,
)
from app.services.shariah import EstimateService, EvidenceService

router = APIRouter(prefix="/workflows", tags=["shariah-pilot"])


def check_dec05_gate(enabled: bool = False) -> None:
    """Check DEC-05 Shariah pilot gate.
    
    Feature is default OFF. Returns 503 if gate is disabled.
    
    Args:
        enabled: DEC-05 gate status (default OFF)
        
    Raises:
        HTTPException: 503 FEATURE_DISABLED if gate is OFF
    """
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "FEATURE_DISABLED",
                    "message": "Shariah pilot requires DEC-05 gate enabled",
                    "retryable": False,
                }
            },
        )


@router.post(
    "/{workflow_id}/shariah/estimates",
    response_model=Envelope[ShariahEstimateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_shariah_estimate(
    workflow_id: UUID,
    request: ShariahEstimateRequest,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
    dec05_enabled: bool = False,  # DEC-05 gate: default OFF
) -> Envelope[ShariahEstimateResponse]:
    """Generate Shariah compliance estimate for product.
    
    Architecture API-075 (simplified for U-015).
    
    Generates preliminary technical estimate based on evidence from certified bodies.
    NOT a fatwa, religious ruling, or compliance approval.
    Always includes explicit disclaimer.
    
    Estimate logic:
    - LIKELY_COMPLIANT: all current evidence is COMPLIANT
    - INSUFFICIENT_DATA: no evidence or all expired
    - LIKELY_NON_COMPLIANT: any evidence is NON_COMPLIANT
    
    Requires: shariah:estimate permission, DEC-05 gate enabled
    Returns: 503 FEATURE_DISABLED if DEC-05 is OFF
    """
    # DEC-05 gate check (default OFF)
    check_dec05_gate(dec05_enabled)

    # Authorization
    check_permission(principal, "shariah:estimate")

    # Service
    estimate_service = EstimateService(db)

    try:
        result = await estimate_service.generate_estimate(
            tenant_id=principal.tenant_id,
            product_ref=request.product_ref,
            workflow_id=workflow_id,
        )

        # Build response with explicit disclaimer
        estimate_response = ShariahEstimateResponse(
            estimate_id=UUID(result["estimate_id"]),
            product_ref=result["product_ref"],
            estimate=result["estimate"],
            reasoning=result["reasoning"],
            evidence_count=result["evidence_count"],
            evidence_ids=[UUID(eid) for eid in result["evidence_ids"]],
            disclaimer=result["disclaimer"],
            created_at=result["created_at"],
        )

        return Envelope(
            data=estimate_response,
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000000"),  # Stub
                served_at=result["created_at"],
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "UNCONFIGURED",
                    "message": f"Shariah estimate service unavailable: {str(e)}",
                    "retryable": False,
                }
            },
        )


@router.get(
    "/shariah/evidence/{product_ref}",
    response_model=Envelope[ShariahEvidenceListResponse],
    status_code=status.HTTP_200_OK,
)
async def list_shariah_evidence(
    product_ref: str,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_fixture_principal),
    dec05_enabled: bool = False,  # DEC-05 gate: default OFF
) -> Envelope[ShariahEvidenceListResponse]:
    """List valid Shariah evidence for product.
    
    Architecture API-076 (simplified for U-015).
    
    Returns evidence from certified bodies (AAOIFI, SSB screening reports).
    Only includes non-expired evidence.
    
    Requires: shariah:view permission, DEC-05 gate enabled
    Returns: 503 FEATURE_DISABLED if DEC-05 is OFF
    """
    # DEC-05 gate check (default OFF)
    check_dec05_gate(dec05_enabled)

    # Authorization
    check_permission(principal, "shariah:view")

    # Service
    evidence_service = EvidenceService(db)

    try:
        result = await evidence_service.fetch_evidence(
            tenant_id=principal.tenant_id,
            product_ref=product_ref,
            dec_05_enabled=dec05_enabled,
            provider_configured=False,  # No live provider for U-015
        )

        # UNCONFIGURED status: no provider configured
        if result.get("status") == "UNCONFIGURED":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "UNCONFIGURED",
                        "message": result["message"],
                        "retryable": False,
                    }
                },
            )

        # Build evidence list response
        evidence_list = [
            ShariahEvidenceDetail(
                evidence_type=ev["evidence_type"],
                source_url=ev["source_url"],
                captured_at=ev["captured_at"],
                expires_at=ev["expires_at"],
                certification_body=ev["certification_body"],
                compliance_status=ev["compliance_status"],
            )
            for ev in result["evidence"]
        ]

        evidence_response = ShariahEvidenceListResponse(
            product_ref=product_ref,
            evidence_count=len(evidence_list),
            evidence=evidence_list,
        )

        return Envelope(
            data=evidence_response,
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000000"),  # Stub
                served_at=datetime.utcnow(),
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "UNAVAILABLE",
                    "message": f"Evidence service unavailable: {str(e)}",
                    "retryable": False,
                }
            },
        )
