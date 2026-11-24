"""Client memory endpoints (API-013, API-014) and conversation history.

Previously both memory endpoints were stubs: GET always returned ``[]`` and
POST raised ``501 NOT_IMPLEMENTED``. They now read/write real rows in
``client_memory_records`` with tenant scoping and an explicit review state.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentPrincipal, VerifiedCSRF
from app.core.authorization import check_permission
from app.core.database import get_db
from app.models.memory import ClientMemoryRecord
from app.models.models import Client, Interaction
from app.schemas.common import Envelope, ResponseMeta
from app.schemas.memory import ConversationRead, MemoryProposalCreate, MemoryRecordRead

router = APIRouter(tags=["memory"])


def _meta() -> ResponseMeta:
    """Build response metadata from real values, not fixture placeholders."""
    return ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))


def _not_found(client_id: UUID) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": {
                "code": "CLIENT_NOT_FOUND",
                "message": f"Client {client_id} was not found in this tenant.",
                "retryable": False,
            }
        },
    )


async def _require_client(db: AsyncSession, tenant_id: str, client_id: UUID) -> Client:
    stmt = select(Client).where(Client.id == client_id, Client.tenant_id == tenant_id)
    client = (await db.execute(stmt)).scalar_one_or_none()
    if client is None:
        raise _not_found(client_id)
    return client


def _to_read(row: ClientMemoryRecord) -> MemoryRecordRead:
    return MemoryRecordRead(
        id=row.id,
        client_id=row.client_id,
        entry_type=row.entry_type,
        content=row.content,
        source_ref=row.source_ref,
        state=row.state,
        confidence=row.confidence,
        proposed_by=row.proposed_by,
        proposed_at=row.proposed_at,
        reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at,
        review_note=row.review_note,
        created_at=row.created_at,
    )


@router.get(
    "/clients/{client_id}/memory",
    response_model=Envelope[list[MemoryRecordRead]],
)
async def get_client_memory(
    client_id: UUID,
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[MemoryRecordRead]]:
    """Return CONFIRMED memory facts for this client (API-013).

    Proposals are deliberately excluded: an unapproved suggestion is not a
    fact about the client.
    """
    check_permission(principal, "memory:read")
    await _require_client(db, principal.tenant_id, client_id)

    stmt = (
        select(ClientMemoryRecord)
        .where(
            ClientMemoryRecord.tenant_id == principal.tenant_id,
            ClientMemoryRecord.client_id == client_id,
            ClientMemoryRecord.state == "CONFIRMED",
        )
        .order_by(ClientMemoryRecord.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return Envelope(data=[_to_read(r) for r in rows], meta=_meta())


@router.get(
    "/clients/{client_id}/memory/proposals",
    response_model=Envelope[list[MemoryRecordRead]],
)
async def list_memory_proposals(
    client_id: UUID,
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[MemoryRecordRead]]:
    """Return pending (NEEDS_REVIEW) memory proposals for this client."""
    check_permission(principal, "memory:read")
    await _require_client(db, principal.tenant_id, client_id)

    stmt = (
        select(ClientMemoryRecord)
        .where(
            ClientMemoryRecord.tenant_id == principal.tenant_id,
            ClientMemoryRecord.client_id == client_id,
            ClientMemoryRecord.state == "NEEDS_REVIEW",
        )
        .order_by(ClientMemoryRecord.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return Envelope(data=[_to_read(r) for r in rows], meta=_meta())


@router.post(
    "/clients/{client_id}/memory/proposals",
    response_model=Envelope[MemoryRecordRead],
    status_code=status.HTTP_201_CREATED,
)
async def propose_memory_entry(
    client_id: UUID,
    request: MemoryProposalCreate,
    principal: CurrentPrincipal,
    csrf: VerifiedCSRF,
    db: AsyncSession = Depends(get_db),
) -> Envelope[MemoryRecordRead]:
    """Create a memory proposal for RM review (API-014).

    A proposal is never confirmed automatically. It persists with
    state=NEEDS_REVIEW and only becomes a confirmed memory entry after review.
    """
    check_permission(principal, "memory:propose")
    await _require_client(db, principal.tenant_id, client_id)

    now = datetime.now(UTC)
    row = ClientMemoryRecord(
        id=uuid4(),
        tenant_id=principal.tenant_id,
        client_id=client_id,
        entry_type=request.kind,
        content=request.content.strip(),
        source_ref=request.source_ref.strip(),
        state="NEEDS_REVIEW",
        confidence=None,
        proposed_by=principal.subject,
        proposed_at=now,
        reviewed_by=None,
        reviewed_at=None,
        review_note=None,
        created_at=now,
    )
    db.add(row)
    await db.commit()
    return Envelope(data=_to_read(row), meta=_meta())


@router.get(
    "/clients/{client_id}/conversations",
    response_model=Envelope[list[ConversationRead]],
)
async def get_client_conversations(
    client_id: UUID,
    principal: CurrentPrincipal,
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[ConversationRead]]:
    """Return the client's interaction / conversation history.

    Backed by the existing ``interactions`` table (RM meeting and call notes),
    not by the demo-client ``client_conversations`` table, which belongs to a
    different client universe and has its own FK to demo_clients.
    """
    check_permission(principal, "client:read")
    await _require_client(db, principal.tenant_id, client_id)

    stmt = (
        select(Interaction)
        .where(Interaction.client_id == client_id)
        .order_by(Interaction.interaction_date.desc())
        .limit(50)
    )
    rows = (await db.execute(stmt)).scalars().all()
    data = [
        ConversationRead(
            id=r.id,
            client_id=r.client_id,
            interaction_date=r.interaction_date,
            interaction_type=r.interaction_type,
            summary=r.summary,
            preferences_extracted=r.preferences_extracted,
            action_items=r.action_items,
            recording_consent=r.recording_consent,
            source_kind=r.source_kind,
            confidence=r.confidence,
        )
        for r in rows
    ]
    return Envelope(data=data, meta=_meta())
