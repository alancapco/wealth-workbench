"""Client memory endpoints (API-013, API-014)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.dependencies import CurrentPrincipal, VerifiedCSRF
from app.core.database import get_db
from app.schemas.common import Envelope, ResponseMeta

router = APIRouter(tags=["memory"])


@router.get("/clients/{client_id}/memory")
async def get_client_memory(
    client_id: UUID,
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[list]:
    """Get client memory entries (API-013).
    
    Returns confirmed memory entries for the client.
    Memory entries are facts extracted from meetings and confirmed by RM.
    """
    # TODO: Query ClientMemoryEntry model when implemented
    # Filter by client_id, tenant_id, and state=CONFIRMED
    
    return Envelope(
        data=[],
        meta=ResponseMeta(
            request_id=UUID("00000000-0000-0000-0000-000000000000"),
            served_at=principal.session_expires_at,
        ),
    )


@router.post("/clients/{client_id}/memory/proposals")
async def propose_memory_entry(
    client_id: UUID,
    principal: CurrentPrincipal,
    csrf: VerifiedCSRF,
    db: AsyncSession = Depends(get_db),
):
    """Propose memory entry for review (API-014).
    
    Creates a memory proposal artifact for RM review.
    Requires review approval before memory entry is confirmed.
    """
    # TODO: Implement memory proposal creation
    # 1. Validate client_id belongs to principal's books
    # 2. Create ArtifactLineage with kind=MEMORY_PROPOSAL
    # 3. Create ArtifactRevision with proposal payload
    # 4. Set review_state=NEEDS_REVIEW
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"code": "NOT_IMPLEMENTED", "message": "Memory proposals not yet implemented"},
    )
