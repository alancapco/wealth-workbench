"""Capture API endpoints per Architecture §6.4 (API-034..044)."""
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_principal
from app.core.database import get_db
from app.models.admin import ConfigurationRevision
from app.models.artifact import ArtifactLineage, ArtifactRevision
from app.models.capture import CaptureSession, ConsentRecord
from app.models.workflow import Meeting
from app.schemas.common import Envelope, ResponseMeta
from app.schemas.identity import Principal
from app.services.capture.capture_service import CaptureService
from app.services.capture.consent_service import ConsentService
from app.services.capture.extraction_service import ExtractionService

router = APIRouter()

# Capture/consent rows are FK-bound to (tenant_id, client_id, meeting_id), so the
# principal and the meeting's real client must be resolved before any write.
# get_current_principal resolves via the shared fixture helper in app.core.identity.
_ACTIVE_CAPTURE_STATUSES = ("STARTING", "RECORDING", "PAUSED", "STOPPING")


# Request/Response DTOs per API-034..044
class ConsentDecisionRequest(BaseModel):
    """API-035: POST /meetings/{m}/consents"""
    policy_ref: dict = Field(..., description="ConfigRef: {id, revision, hash}")
    jurisdiction: str
    platform: str
    language: str
    decision: str = Field(..., pattern="^(ACCEPTED|DECLINED)$")
    method: str
    participant_refs: list[str]
    coverage_confirmation: bool


class ConsentWithdrawRequest(BaseModel):
    """API-036: POST /meetings/{m}/consents/{id}/withdraw"""
    reason: Optional[dict] = None


class StartCaptureRequest(BaseModel):
    """API-037: POST /meetings/{m}/captures"""
    consent_id: UUID
    policy_ref: dict  # ConfigRef


class CaptureControlRequest(BaseModel):
    """API-038: POST /captures/{id}/controls"""
    command: str = Field(..., pattern="^(PAUSE|RESUME|STOP)$")


class AppendSegmentRequest(BaseModel):
    """POST /captures/{id}/segments - segment progress tracking"""
    audio_ms: Optional[int] = None
    transcript_ms: Optional[int] = None


class ExtractionEditRequest(BaseModel):
    """API-044: PATCH /extractions/{id}/edits"""
    edits: list[dict]
    suppressed_item_keys: list[str]
    impact_confirmation: bool


# Response DTOs
class ConsentResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    policy_ref: dict
    state: str
    jurisdiction: str
    platform: str
    language: str
    method: str
    participant_refs: list[str]
    actor: str
    recorded_at: datetime
    withdrawn_at: Optional[datetime] = None
    row_version: int


class CaptureResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    consent_id: UUID
    status: str
    row_version: int
    last_confirmed_audio_ms: Optional[int] = None
    last_confirmed_transcript_ms: Optional[int] = None
    provider_ref: Optional[str] = None
    lease_valid_until: Optional[datetime] = None
    error_code: Optional[str] = None


async def _meeting_client_id(db: AsyncSession, tenant_id: str, meeting_id: UUID) -> UUID:
    """Resolve the real client from the meeting (consent/capture FK target)."""
    stmt = select(Meeting.client_id).where(
        Meeting.tenant_id == tenant_id,
        Meeting.id == meeting_id,
    )
    client_id = (await db.execute(stmt)).scalar_one_or_none()
    if client_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return client_id


async def _policy_ref(db: AsyncSession, tenant_id: str, policy_configuration_id: UUID) -> dict:
    """Build a ConfigRef from the stored policy revision; no fabricated hash."""
    stmt = select(ConfigurationRevision).where(
        ConfigurationRevision.tenant_id == tenant_id,
        ConfigurationRevision.id == policy_configuration_id,
    )
    config = (await db.execute(stmt)).scalar_one_or_none()
    if config is None:
        return {"id": str(policy_configuration_id), "revision": None, "hash": None}
    return {"id": str(config.id), "revision": config.revision, "hash": config.content_hash}


def _consent_response(consent: ConsentRecord, policy_ref: dict) -> ConsentResponse:
    return ConsentResponse(
        id=consent.id,
        meeting_id=consent.meeting_id,
        policy_ref=policy_ref,
        state=consent.state,
        jurisdiction=consent.jurisdiction,
        platform=consent.platform,
        language=consent.language,
        method=consent.method,
        participant_refs=consent.participant_refs,
        actor=consent.actor,
        recorded_at=consent.recorded_at,
        withdrawn_at=consent.withdrawn_at,
        row_version=consent.row_version,
    )


def _capture_response(capture: CaptureSession) -> CaptureResponse:
    return CaptureResponse(
        id=capture.id,
        meeting_id=capture.meeting_id,
        consent_id=capture.consent_id,
        status=capture.status,
        row_version=capture.row_version,
        last_confirmed_audio_ms=capture.last_confirmed_audio_ms,
        last_confirmed_transcript_ms=capture.last_confirmed_transcript_ms,
        provider_ref=capture.provider_ref,
        lease_valid_until=capture.lease_valid_until,
        error_code=capture.error_code,
    )


@router.post("/meetings/{meeting_id}/consent", status_code=status.HTTP_201_CREATED)
async def record_consent(
    meeting_id: UUID,
    request: ConsentDecisionRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-035: Record consent decision (ACCEPTED/DECLINED).

    Fail-closed: missing policy blocks consent upstream.
    Calendar acceptance is NOT consent.
    """
    try:
        tenant_id = principal.tenant_id
        client_id = await _meeting_client_id(db, tenant_id, meeting_id)
        policy_configuration_id = UUID(request.policy_ref["id"])
        policy_ref = await _policy_ref(db, tenant_id, policy_configuration_id)
        if policy_ref["hash"] is None:
            raise ValueError("Policy configuration not found")

        consent = await ConsentService(db).record_consent(
            tenant_id=tenant_id,
            client_id=client_id,
            meeting_id=meeting_id,
            policy_configuration_id=policy_configuration_id,
            jurisdiction=request.jurisdiction,
            platform=request.platform,
            language=request.language,
            method=request.method,
            participant_refs=request.participant_refs,
            decision=request.decision,
            actor=principal.subject,
        )

        await db.commit()

        return Envelope(
            data={"consent": _consent_response(consent, policy_ref)},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/meetings/{meeting_id}/consent")
async def get_consent(
    meeting_id: UUID,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-034 (partial): GET current consent for meeting."""
    try:
        tenant_id = principal.tenant_id
        client_id = await _meeting_client_id(db, tenant_id, meeting_id)
        consent = await ConsentService(db).get_current_consent(
            tenant_id=tenant_id,
            client_id=client_id,
            meeting_id=meeting_id,
        )

        if not consent:
            return Envelope(
                data={"consent": None, "blockers": ["NO_CONSENT"]},
                meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
            )

        policy_ref = await _policy_ref(db, tenant_id, consent.policy_configuration_id)
        return Envelope(
            data={"consent": _consent_response(consent, policy_ref), "blockers": []},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/meetings/{meeting_id}/consents/{consent_id}/withdraw")
async def withdraw_consent(
    meeting_id: UUID,
    consent_id: UUID,
    request: ConsentWithdrawRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-036: Withdraw consent and invalidate capture.

    Immediately denies new capture, stops existing capture.
    """
    try:
        tenant_id = principal.tenant_id
        client_id = await _meeting_client_id(db, tenant_id, meeting_id)
        consent = await ConsentService(db).withdraw_consent(
            tenant_id=tenant_id,
            client_id=client_id,
            consent_id=consent_id,
            actor=principal.subject,
        )

        # Compliance: withdrawal must stop every live stream for the meeting, not
        # just mark the consent row, otherwise recording continues without consent.
        active_stmt = select(CaptureSession).where(
            CaptureSession.tenant_id == tenant_id,
            CaptureSession.client_id == client_id,
            CaptureSession.meeting_id == meeting_id,
            CaptureSession.status.in_(_ACTIVE_CAPTURE_STATUSES),
        )
        active_captures = (await db.execute(active_stmt)).scalars().all()
        invalidated_refs = []
        for capture in active_captures:
            capture.status = "STOPPED"
            capture.lease_revoked = True
            capture.row_version += 1
            capture.updated_at = datetime.now(UTC)
            invalidated_refs.append({
                "capture_id": str(capture.id),
                "meeting_id": str(capture.meeting_id),
                "consent_id": str(capture.consent_id),
                "status": capture.status,
                "lease_revoked": capture.lease_revoked,
            })

        await db.commit()

        policy_ref = await _policy_ref(db, tenant_id, consent.policy_configuration_id)
        return Envelope(
            data={
                "consent": _consent_response(consent, policy_ref),
                "capture": None,
                "invalidated_refs": invalidated_refs,
            },
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/meetings/{meeting_id}/capture/start", status_code=status.HTTP_202_ACCEPTED)
async def start_capture(
    meeting_id: UUID,
    request: StartCaptureRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-037: Start capture with accepted consent."""
    try:
        tenant_id = principal.tenant_id
        client_id = await _meeting_client_id(db, tenant_id, meeting_id)
        capture = await CaptureService(db).start_capture(
            tenant_id=tenant_id,
            client_id=client_id,
            meeting_id=meeting_id,
            consent_id=request.consent_id,
            provider_key="test-provider",
            actor=principal.subject,
        )

        await db.commit()

        return Envelope(
            data={"capture": _capture_response(capture)},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/meetings/{meeting_id}/capture/segments")
async def append_segments(
    meeting_id: UUID,
    request: AppendSegmentRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Append segment progress (audio_ms, transcript_ms).

    Append-only: never decreases positions.
    """
    try:
        tenant_id = principal.tenant_id
        active_stmt = select(CaptureSession).where(
            CaptureSession.tenant_id == tenant_id,
            CaptureSession.meeting_id == meeting_id,
            CaptureSession.status.in_(_ACTIVE_CAPTURE_STATUSES),
        ).order_by(CaptureSession.created_at.desc()).limit(1)
        capture = (await db.execute(active_stmt)).scalar_one_or_none()
        if capture is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active capture for this meeting",
            )

        capture = await CaptureService(db).append_segment_progress(
            tenant_id=tenant_id,
            client_id=capture.client_id,
            capture_id=capture.id,
            audio_ms=request.audio_ms,
            transcript_ms=request.transcript_ms,
        )

        await db.commit()

        return Envelope(
            data={"capture": _capture_response(capture)},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/extractions/{extraction_id}/edits", status_code=status.HTTP_201_CREATED)
async def apply_extraction_edits(
    extraction_id: UUID,
    request: ExtractionEditRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-044: Apply RM corrections to extraction.

    Creates immutable new revision with RM_ENTERED origin.
    Preserves original evidence, adds correction reason.
    """
    try:
        tenant_id = principal.tenant_id
        lineage_stmt = select(ArtifactLineage).where(
            ArtifactLineage.tenant_id == tenant_id,
            ArtifactLineage.id == extraction_id,
        )
        lineage = (await db.execute(lineage_stmt)).scalar_one_or_none()
        if lineage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")

        # The lineage pointer is authoritative; fall back to the highest version
        # when a legacy row never set current_revision_id.
        revision_stmt = select(ArtifactRevision).where(
            ArtifactRevision.tenant_id == tenant_id,
            ArtifactRevision.client_id == lineage.client_id,
            ArtifactRevision.artifact_id == extraction_id,
        )
        if lineage.current_revision_id is not None:
            revision_stmt = revision_stmt.where(
                ArtifactRevision.id == lineage.current_revision_id
            )
        else:
            revision_stmt = revision_stmt.order_by(ArtifactRevision.version.desc()).limit(1)
        current_revision = (await db.execute(revision_stmt)).scalar_one_or_none()
        if current_revision is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current extraction revision not found",
            )

        new_revision = await ExtractionService(db).apply_extraction_edits(
            tenant_id=tenant_id,
            client_id=lineage.client_id,
            artifact_id=extraction_id,
            current_revision_id=current_revision.id,
            edits=request.edits,
            suppressed_item_keys=request.suppressed_item_keys,
            actor=principal.subject,
        )
        lineage.current_revision_id = new_revision.id

        await db.commit()

        return Envelope(
            data={
                "artifact": {
                    "id": new_revision.artifact_id,
                    "revision_id": new_revision.id,
                    "version": new_revision.version,
                    "content_hash": new_revision.content_hash,
                    "payload": new_revision.payload,
                },
                # No downstream dependency rows are linked to extraction revisions yet.
                "invalidated_refs": [],
            },
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.now(UTC))
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
