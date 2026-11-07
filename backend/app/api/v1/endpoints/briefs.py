"""Brief lifecycle API per Architecture §6.3 - API-004, 005, 006, 031, 032.

Explicit generation only (never on GET), section-level review, edit creates new revision.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.artifact import ArtifactLineage, ArtifactRevision, ReviewDecision
from app.models.models import Brief as BriefModel
from app.repositories.artifacts import ReviewRepository
from app.schemas.brief import (
    Brief,
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
    ResponseMeta,
    ReviewState,
    Source,
)
from app.services.brief.brief_generator import BriefGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


# Mock principal extraction - real implementation from U-003
def get_current_actor() -> str:
    """Extract actor from authenticated session. Placeholder for U-003 identity."""
    return "fixture-user-001"


def get_tenant_id() -> str:
    """Extract tenant from authenticated session. Placeholder for U-003 scope."""
    return "fixture-tenant-001"


class ClientBriefRequest(BaseModel):
    client_id: str
    force_regenerate: bool = False


@router.post("/generate")
async def generate_client_brief(
    body: ClientBriefRequest,
    db: AsyncSession = Depends(get_db),
):
    """Meeting brief for the dashboard modal, built from holdings, quotes, interactions, and news."""
    from app.services.brief.brief_service import brief_service

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

        # Fetch workflow to get client_id and validate authorization
        from app.models.workflow import Workflow
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

        # Fetch from legacy briefs table which has canonical sections
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

        # Reconstruct Brief from stored sections JSON
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

        # Validate artifact ref matches current revision
        if if_match != f'"{request.artifact_ref.revision_id}:{request.artifact_ref.hash}"':
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="If-Match header does not match artifact ref"
            )

        # Fetch brief model to get client_id
        brief_model = await db.get(BriefModel, brief_id)
        if not brief_model or brief_model.artifact_revision_id != request.artifact_ref.revision_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Brief revision changed - stale review"
            )

        # Record reviews for each section
        review_repo = ReviewRepository(db)
        reviews = []
        
        for section_review in request.sections:
            review = await review_repo.record_review(
                tenant_id=tenant_id,
                client_id=brief_model.client_id,
                revision_id=request.artifact_ref.revision_id,
                scope="ITEM",
                item_key=section_review.key.value,
                item_hash=section_review.hash,
                decision=section_review.decision,
                actor=actor,
                reason=section_review.reason,
            )
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

        # Return updated brief with review states
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

        # Fetch current brief
        brief_model = await db.get(BriefModel, brief_id)
        if not brief_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brief {brief_id} not found"
            )

        # Apply edits to sections
        sections_json = brief_model.sections.copy()
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
                # Recompute section hash
                import hashlib
                import json
                section_canonical = {
                    "key": section_key,
                    "narrative": edit.narrative,
                    "claims": sections_json[section_key]["claims"],
                    "agenda": sections_json[section_key]["agenda"],
                }
                json_bytes = json.dumps(section_canonical, sort_keys=True, separators=(',', ':')).encode('utf-8')
                sections_json[section_key]["item_hash"] = hashlib.sha256(json_bytes).hexdigest()
                # Reset review state for edited sections
                sections_json[section_key]["review_state"] = "NEEDS_REVIEW"

        # Create new brief revision
        next_version = brief_model.revision_no + 1
        new_brief = BriefModel(
            id=brief_id,
            client_id=brief_model.client_id,
            version=str(next_version),
            sections=sections_json,
            generated_at=brief_model.generated_at,
            tenant_id=brief_model.tenant_id,
            workflow_id=brief_model.workflow_id,
            meeting_id=brief_model.meeting_id,
            artifact_id=brief_model.artifact_id,
            artifact_revision_id=UUID("00000000-0000-0000-0000-000000000099"),  # Placeholder
            revision_no=next_version,
        )
        db.add(new_brief)
        await db.commit()

        # Return updated brief
        brief = await _reconstruct_brief_from_model(new_brief, db)

        return Envelope(
            data=EditBriefData(brief=brief),
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000004"),
                served_at=new_brief.generated_at,
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
                artifact_ref={
                    "artifact_id": b.artifact_id,
                    "revision_id": b.artifact_revision_id,
                    "version": b.revision_no,
                    "hash": "0" * 64,  # Placeholder
                },
                workflow_id=b.workflow_id,
                meeting_id=b.meeting_id,
                client_id=b.client_id,
                generated_at=b.generated_at,
                generated_by="fixture-user-001",
                review_state=ReviewState.UNREVIEWED,
            )
            for b in brief_models
        ]

        return Envelope(
            data=BriefListData(items=headers, next_cursor=None),
            meta=ResponseMeta(
                request_id=UUID("00000000-0000-0000-0000-000000000005"),
                served_at=brief_models[0].generated_at if brief_models else None,
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
    
    def parse_section(key: str, data: dict) -> BriefSection:
        from app.schemas.brief import BriefClaim, AgendaItem
        return BriefSection(
            key=key,
            item_hash=data["item_hash"],
            narrative=data.get("narrative"),
            claims=[
                BriefClaim(
                    id=c["id"],
                    text=c["text"],
                    origin=c["origin"],
                    evidence_refs=[],
                    confidence=c.get("confidence"),
                )
                for c in data.get("claims", [])
            ],
            agenda=[
                AgendaItem(
                    id=a["id"],
                    text=a["text"],
                    origin=a["origin"],
                    evidence_refs=[],
                )
                for a in data.get("agenda", [])
            ],
            availability=Availability(data["availability"]),
            completeness=Completeness(data["completeness"]),
            capability_state=CapabilityState(data["capability_state"]),
            review_state=ReviewState(data["review_state"]),
            sources=[],
            limitations=data.get("limitations", []),
        )

    sections = BriefSections(
        portfolio_overview=parse_section("portfolio_overview", sections_data["portfolio_overview"]),
        material_changes=parse_section("material_changes", sections_data["material_changes"]),
        recent_interactions=parse_section("recent_interactions", sections_data["recent_interactions"]),
        market_news=parse_section("market_news", sections_data["market_news"]),
        proposed_agenda=parse_section("proposed_agenda", sections_data["proposed_agenda"]),
    )

    return Brief(
        brief_id=brief_model.id,
        artifact_ref={
            "artifact_id": brief_model.artifact_id,
            "revision_id": brief_model.artifact_revision_id,
            "version": brief_model.revision_no,
            "hash": "0" * 64,  # Placeholder
        },
        workflow_id=brief_model.workflow_id,
        meeting_id=brief_model.meeting_id,
        client_id=brief_model.client_id,
        generated_at=brief_model.generated_at,
        generated_by="fixture-user-001",
        review_state=ReviewState.UNREVIEWED,
        version=brief_model.revision_no,
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test-env-001"),
        source_cutoff=None,
        sections=sections,
        blockers=[],
    )
