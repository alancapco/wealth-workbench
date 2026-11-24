"""Brief lifecycle API per Architecture §6.3 - API-004, 005, 006, 031, 032.

Explicit generation only (never on GET), section-level review, edit creates new revision.
"""
import json
import logging
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.identity import get_fixture_principal
from app.models.artifact import ArtifactItem, ArtifactLineage, ArtifactRevision, ReviewDecision
from app.models.models import Brief as BriefModel
from app.models.workflow import Workflow
from app.schemas.brief import (
    AgendaItem,
    Brief,
    BriefClaim,
    BriefHeader,
    BriefListData,
    BriefSection,
    BriefSections,
    EditBriefData,
    EditBriefRequest,
    GenerateBriefData,
    GenerateBriefRequest,
    GetBriefData,
    ReviewBriefData,
    ReviewBriefRequest,
)
from app.schemas.common import (
    Availability,
    CapabilityState,
    Completeness,
    Envelope,
    Environment,
    EnvironmentKind,
    EvidenceRef,
    ResponseMeta,
    ReviewState,
    Source,
)
from app.services.brief.brief_generator import BriefArtifactRef, BriefGenerator, canonical_hash
from app.services.brief.brief_service import brief_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Fixture identity is the single source of truth for actor/tenant (see app/core/identity.py).
def get_current_actor() -> str:
    """Current authenticated actor from the shared fixture principal."""
    return get_fixture_principal().subject


def get_tenant_id() -> str:
    """Current tenant scope from the shared fixture principal."""
    return get_fixture_principal().tenant_id


class ClientBriefRequest(BaseModel):
    client_id: str
    force_regenerate: bool = False


def _parse_uuid(value: str, field: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")


def _brief_version(brief_model: BriefModel) -> int:
    if brief_model.revision_no:
        return brief_model.revision_no
    try:
        return max(1, int(brief_model.version))
    except (TypeError, ValueError):
        return 1


def _artifact_ref(brief_model: BriefModel) -> BriefArtifactRef:
    """Resolve the real content hash over the stored canonical sections JSON."""
    # Legacy rows predate artifact linkage; their own id is the only real identifier.
    return BriefArtifactRef(
        artifact_id=brief_model.artifact_id or brief_model.id,
        revision_id=brief_model.artifact_revision_id or brief_model.id,
        version=_brief_version(brief_model),
        hash=canonical_hash(brief_model.sections),
    )


@router.get("")
async def list_briefs_by_client(
    client_id: Optional[str] = Query(None),
    workflow_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """GET /briefs - List briefs for a client (API-004 list variant)"""
    tenant_id = get_tenant_id()
    stmt = select(BriefModel).where(
        or_(BriefModel.tenant_id == tenant_id, BriefModel.tenant_id.is_(None))
    )
    if client_id:
        stmt = stmt.where(BriefModel.client_id == _parse_uuid(client_id, "client_id"))
    if workflow_id:
        stmt = stmt.where(BriefModel.workflow_id == _parse_uuid(workflow_id, "workflow_id"))

    stmt = stmt.order_by(BriefModel.generated_at.desc()).limit(50)
    result = await db.execute(stmt)
    brief_models = result.scalars().all()

    data = []
    for b in brief_models:
        ref = _artifact_ref(b)
        data.append({
            "brief_id": str(b.id),
            "artifact_ref": {
                "artifact_id": str(ref["artifact_id"]),
                "revision_id": str(ref["revision_id"]),
                "version": ref["version"],
                "hash": ref["hash"],
            },
            "workflow_id": str(b.workflow_id) if b.workflow_id else None,
            "meeting_id": str(b.meeting_id) if b.meeting_id else None,
            "client_id": str(b.client_id),
            "generated_at": b.generated_at.isoformat() if b.generated_at else None,
            "generated_by": b.generated_by or get_current_actor(),
            "review_state": ReviewState.UNREVIEWED.value,
        })

    return {"data": data, "meta": {"request_id": str(uuid4()), "served_at": datetime.now(UTC).isoformat()}}


@router.post("/generate")
async def generate_client_brief(
    body: ClientBriefRequest,
    db: AsyncSession = Depends(get_db),
):
    """Meeting brief for the dashboard modal, built from holdings, quotes, interactions, and news."""
    try:
        brief = await brief_service.generate_brief(body.client_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating client brief: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error generating brief")

    sections = brief.pop("sections")
    return {"brief": {**brief, **sections}}


@router.post("/briefs", status_code=status.HTTP_201_CREATED)
async def generate_brief(
    request: GenerateBriefRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> Envelope[GenerateBriefData]:
    """POST /briefs - Generate brief explicitly per API-004.

    Never generates on GET/reload. Uses frozen workflow context from U-006.
    Returns 201 with brief or 202 with stage run if queued.
    """
    try:
        actor = get_current_actor()
        tenant_id = get_tenant_id()

        workflow = await db.get(Workflow, request.workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {request.workflow_id} not found"
            )

        generator = BriefGenerator(db)
        brief = await generator.generate_brief(
            tenant_id=tenant_id,
            client_id=workflow.client_id,
            workflow_id=request.workflow_id,
            meeting_id=request.meeting_id,
            section_keys=[k.value for k in request.section_keys],
            actor=actor,
            previous_artifact_id=request.previous_ref.artifact_id if request.previous_ref else None,
        )

        return Envelope(
            data=GenerateBriefData(brief=brief),
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000001"),
                served_at=brief.generated_at,
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating brief: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error generating brief"
        )


@router.get("/briefs/{brief_id}")
async def get_brief(
    brief_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Envelope[GetBriefData]:
    """GET /briefs/{brief_id} - Fetch existing brief per API-005.

    Never generates. Returns current revision with sections from briefs.sections.
    """
    try:
        tenant_id = get_tenant_id()

        stmt = select(BriefModel).where(
            BriefModel.id == brief_id,
            BriefModel.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        brief_model = result.scalar_one_or_none()

        if not brief_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brief {brief_id} not found"
            )

        brief = await _reconstruct_brief_from_model(brief_model, db)

        return Envelope(
            data=GetBriefData(brief=brief),
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000002"),
                served_at=brief_model.generated_at,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brief {brief_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error fetching brief"
        )


@router.post("/briefs/{brief_id}/reviews")
async def review_brief(
    brief_id: UUID,
    request: ReviewBriefRequest,
    if_match: str = Header(..., alias="If-Match"),
    db: AsyncSession = Depends(get_db),
) -> Envelope[ReviewBriefData]:
    """POST /briefs/{brief_id}/reviews - Section-level review per API-006.

    Reviews exact current section hashes. Stale hash returns 409.
    """
    try:
        actor = get_current_actor()
        tenant_id = get_tenant_id()

        brief_model = await db.get(BriefModel, brief_id)
        if not brief_model or brief_model.artifact_revision_id != request.artifact_ref.revision_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Brief revision changed - stale review"
            )

        # The real content hash makes If-Match meaningful: reject stale content.
        stored_hash = canonical_hash(brief_model.sections)
        if (if_match != f'"{request.artifact_ref.revision_id}:{request.artifact_ref.hash}"'
                or request.artifact_ref.hash != stored_hash):
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="If-Match header does not match current brief content"
            )

        # Reviews must reference the current section hashes; a stale hash would
        # violate the review_decisions -> artifact_items FK and surface as a 500.
        for section_review in request.sections:
            stored_section = brief_model.sections.get(section_review.key.value)
            if not stored_section or stored_section.get("item_hash") != section_review.hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Section {section_review.key.value} hash changed - stale review"
                )

        reviews = []

        for section_review in request.sections:
            # Explicit id keeps the review id available in the response without an extra flush.
            review = ReviewDecision(
                id=uuid4(),
                tenant_id=tenant_id,
                client_id=brief_model.client_id,
                revision_id=request.artifact_ref.revision_id,
                scope="ITEM",
                item_key=section_review.key.value,
                item_hash=section_review.hash,
                decision=section_review.decision,
                actor=actor,
                reason=section_review.reason,
                recorded_at=datetime.now(UTC),
            )
            db.add(review)
            reviews.append({
                "id": str(review.id),
                "scope": "ITEM",
                "item_key": section_review.key.value,
                "item_hash": section_review.hash,
                "decision": section_review.decision,
                "actor": actor,
                "at": review.recorded_at.isoformat(),
                "reason": section_review.reason,
            })

        await db.commit()

        brief = await _reconstruct_brief_from_model(brief_model, db)

        return Envelope(
            data=ReviewBriefData(brief=brief, reviews=reviews),
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000003"),
                served_at=brief_model.generated_at,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing brief {brief_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error reviewing brief"
        )


@router.patch("/briefs/{brief_id}", status_code=status.HTTP_201_CREATED)
async def edit_brief(
    brief_id: UUID,
    request: EditBriefRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[EditBriefData]:
    """PATCH /briefs/{brief_id} - Edit creates new revision per API-032.

    Edits narrative/agenda only, never holdings/source data. Creates new revision,
    does not inherit reviews. Unaffected sections preserve content but not approval.
    """
    try:
        actor = get_current_actor()
        tenant_id = get_tenant_id()

        brief_model = await db.get(BriefModel, brief_id)
        if not brief_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brief {brief_id} not found"
            )

        sections_json = {key: dict(section) for key, section in brief_model.sections.items()}
        for edit in request.section_edits:
            section_key = edit.key.value
            if section_key in sections_json:
                sections_json[section_key]["narrative"] = edit.narrative
                if edit.agenda is not None:
                    sections_json[section_key]["agenda"] = [
                        {
                            "id": a.id,
                            "text": a.text,
                            "origin": a.origin.value,
                            "evidence_refs": [
                                {"source_id": str(e.source_id), "source_version": e.source_version}
                                for e in a.evidence_refs
                            ],
                        }
                        for a in edit.agenda
                    ]
                canonical = {
                    "key": section_key,
                    "narrative": edit.narrative,
                    "claims": [
                        {"id": c["id"], "text": c["text"], "origin": c["origin"]}
                        for c in sections_json[section_key]["claims"]
                    ],
                    "agenda": [
                        {"id": a["id"], "text": a["text"], "origin": a["origin"]}
                        for a in sections_json[section_key]["agenda"]
                    ],
                }
                sections_json[section_key]["item_hash"] = canonical_hash(canonical)
                sections_json[section_key]["review_state"] = "NEEDS_REVIEW"

        current_revision = (
            await db.get(ArtifactRevision, brief_model.artifact_revision_id)
            if brief_model.artifact_revision_id else None
        )
        next_version = (current_revision.version + 1) if current_revision else _brief_version(brief_model) + 1
        revision = ArtifactRevision(
            id=uuid4(),
            tenant_id=tenant_id,
            client_id=brief_model.client_id,
            artifact_id=brief_model.artifact_id or brief_id,
            version=next_version,
            content_hash=canonical_hash(sections_json),
            payload=json.dumps({"brief_id": str(brief_id), "sections": sections_json}),
            environment_kind="FIXTURE",
            environment_id="test-env-001",
            created_by=actor,
            created_at=datetime.now(UTC),
        )
        db.add(revision)
        # App sessions run with autoflush=False; the composite FK on artifact_items
        # is not ordered by the unit of work, so persist the revision first.
        await db.flush()

        lineage = await db.get(ArtifactLineage, brief_model.artifact_id or brief_id)
        if lineage:
            lineage.current_revision_id = revision.id

        for key, section in sections_json.items():
            db.add(ArtifactItem(
                tenant_id=tenant_id,
                client_id=brief_model.client_id,
                revision_id=revision.id,
                item_key=key,
                item_hash=section["item_hash"],
                status=section.get("review_state", "UNREVIEWED"),
            ))

        # Update in place: briefs.id is the primary key, so a second insert would collide.
        brief_model.sections = sections_json
        brief_model.version = str(next_version)
        brief_model.revision_no = next_version
        brief_model.artifact_revision_id = revision.id
        brief_model.content_hash = revision.content_hash
        brief_model.generated_by = actor
        await db.commit()

        brief = await _reconstruct_brief_from_model(brief_model, db)

        return Envelope(
            data=EditBriefData(brief=brief),
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000004"),
                served_at=brief_model.generated_at,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing brief {brief_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error editing brief"
        )


@router.get("/workflows/{workflow_id}/briefs")
async def list_briefs(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Envelope[BriefListData]:
    """GET /workflows/{w}/briefs - List briefs for workflow per API-031."""
    try:
        tenant_id = get_tenant_id()

        stmt = (
            select(BriefModel)
            .where(
                BriefModel.workflow_id == workflow_id,
                BriefModel.tenant_id == tenant_id,
            )
            .order_by(BriefModel.generated_at.desc())
            .limit(50)
        )
        result = await db.execute(stmt)
        brief_models = result.scalars().all()

        headers = [
            BriefHeader(
                brief_id=b.id,
                artifact_ref=_artifact_ref(b),
                workflow_id=b.workflow_id,
                meeting_id=b.meeting_id,
                client_id=b.client_id,
                generated_at=b.generated_at,
                generated_by=b.generated_by or get_current_actor(),
                review_state=ReviewState.UNREVIEWED,
            )
            for b in brief_models
        ]

        return Envelope(
            data=BriefListData(items=headers, next_cursor=None),
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000005"),
                served_at=datetime.now(UTC),
            ),
        )

    except Exception as e:
        logger.error(f"Error listing briefs for workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error listing briefs"
        )


async def _reconstruct_brief_from_model(brief_model: BriefModel, db: AsyncSession) -> Brief:
    """Reconstruct Brief DTO from stored BriefModel with sections JSON."""
    sections_data = brief_model.sections

    def parse_evidence(data: dict) -> list[EvidenceRef]:
        return [EvidenceRef(**ref) for ref in data.get("evidence_refs", [])]

    def parse_source(data: dict) -> Source:
        fields = {
            "id", "environment", "availability", "origin", "system_key", "record_id",
            "record_version", "as_of", "retrieved_at", "authoritative_owner",
            "live_response", "adapter_receipt_id", "confidence", "limitation_codes",
        }
        return Source(**{k: v for k, v in data.items() if k in fields})

    def parse_section(key: str, data: dict) -> BriefSection:
        return BriefSection(
            key=key,
            item_hash=data["item_hash"],
            narrative=data.get("narrative"),
            claims=[
                BriefClaim(
                    id=c["id"],
                    text=c["text"],
                    origin=c["origin"],
                    evidence_refs=parse_evidence(c),
                    confidence=c.get("confidence"),
                )
                for c in data.get("claims", [])
            ],
            agenda=[
                AgendaItem(
                    id=a["id"],
                    text=a["text"],
                    origin=a["origin"],
                    evidence_refs=parse_evidence(a),
                )
                for a in data.get("agenda", [])
            ],
            availability=Availability(data["availability"]),
            completeness=Completeness(data["completeness"]),
            capability_state=CapabilityState(data["capability_state"]),
            review_state=ReviewState(data.get("review_state", "UNREVIEWED")),
            sources=[parse_source(s) for s in data.get("sources", [])],
            limitations=data.get("limitations", []),
        )

    sections = BriefSections(
        portfolio_overview=parse_section("portfolio_overview", sections_data["portfolio_overview"]),
        material_changes=parse_section("material_changes", sections_data["material_changes"]),
        recent_interactions=parse_section("recent_interactions", sections_data["recent_interactions"]),
        market_news=parse_section("market_news", sections_data["market_news"]),
        proposed_agenda=parse_section("proposed_agenda", sections_data["proposed_agenda"]),
    )

    revision = (
        await db.get(ArtifactRevision, brief_model.artifact_revision_id)
        if brief_model.artifact_revision_id else None
    )
    environment = (
        Environment(kind=EnvironmentKind(revision.environment_kind), id=revision.environment_id)
        if revision else Environment(kind=EnvironmentKind.FIXTURE, id="test-env-001")
    )

    return Brief(
        brief_id=brief_model.id,
        artifact_ref=_artifact_ref(brief_model),
        workflow_id=brief_model.workflow_id,
        meeting_id=brief_model.meeting_id,
        client_id=brief_model.client_id,
        generated_at=brief_model.generated_at,
        generated_by=brief_model.generated_by or get_current_actor(),
        review_state=ReviewState.UNREVIEWED,
        version=_brief_version(brief_model),
        environment=environment,
        source_cutoff=revision.created_at if revision else None,
        sections=sections,
        blockers=[],
    )
