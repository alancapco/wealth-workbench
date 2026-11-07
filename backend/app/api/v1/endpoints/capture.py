"""Capture API endpoints per Architecture §6.4 (API-034..044)."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.capture import CaptureSession, ConsentRecord
from app.schemas.common import Envelope, ResponseMeta
from app.services.capture.capture_service import CaptureService
from app.services.capture.consent_service import ConsentService
from app.services.capture.extraction_service import ExtractionService

router = APIRouter()

# Mock principal for testing
MOCK_TENANT = "test-tenant"
MOCK_ACTOR = "test-rm"
MOCK_PERMISSIONS = ["consent:record", "consent:withdraw", "capture:start", "capture:control", "capture:read"]


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


@router.post("/meetings/{meeting_id}/consent", status_code=status.HTTP_201_CREATED)
async def record_consent(
    meeting_id: UUID,
    request: ConsentDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-035: Record consent decision (ACCEPTED/DECLINED).
    
    Fail-closed: missing policy blocks consent upstream.
    Calendar acceptance is NOT consent.
    """
    try:
        # Mock client_id (would come from meeting lookup + authorization)
        client_id = uuid4()
        
        consent_service = ConsentService(db)
        
        consent_id = uuid4()
        consent = await consent_service.record_consent(
            tenant_id=MOCK_TENANT,
            client_id=client_id,
            meeting_id=meeting_id,
            policy_configuration_id=UUID(request.policy_ref["id"]),
            jurisdiction=request.jurisdiction,
            platform=request.platform,
            language=request.language,
            method=request.method,
            participant_refs=request.participant_refs,
            decision=request.decision,
            actor=MOCK_ACTOR,
        )
        consent.id = consent_id  # Set after creation
        
        await db.commit()
        
        response = ConsentResponse(
            id=consent.id,
            meeting_id=consent.meeting_id,
            policy_ref=request.policy_ref,
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
        
        return Envelope(
            data={"consent": response},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/meetings/{meeting_id}/consent")
async def get_consent(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-034 (partial): GET current consent for meeting."""
    try:
        client_id = uuid4()  # Mock
        consent_service = ConsentService(db)
        
        consent = await consent_service.get_current_consent(
            tenant_id=MOCK_TENANT,
            client_id=client_id,
            meeting_id=meeting_id,
        )
        
        if not consent:
            return Envelope(
                data={"consent": None, "blockers": ["NO_CONSENT"]},
                meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
            )
        
        response = ConsentResponse(
            id=consent.id,
            meeting_id=consent.meeting_id,
            policy_ref={"id": str(consent.policy_configuration_id), "revision": 1, "hash": "mock"},
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
        
        return Envelope(
            data={"consent": response, "blockers": []},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/meetings/{meeting_id}/consents/{consent_id}/withdraw")
async def withdraw_consent(
    meeting_id: UUID,
    consent_id: UUID,
    request: ConsentWithdrawRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-036: Withdraw consent and invalidate capture.
    
    Immediately denies new capture, stops existing capture.
    """
    try:
        client_id = uuid4()  # Mock
        consent_service = ConsentService(db)
        capture_service = CaptureService(db)
        
        consent = await consent_service.withdraw_consent(
            tenant_id=MOCK_TENANT,
            client_id=client_id,
            consent_id=consent_id,
            actor=MOCK_ACTOR,
        )
        
        # Revoke any active captures
        # (simplified - full impl would query and revoke all active captures)
        
        await db.commit()
        
        response = ConsentResponse(
            id=consent.id,
            meeting_id=consent.meeting_id,
            policy_ref={"id": str(consent.policy_configuration_id), "revision": 1, "hash": "mock"},
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
        
        return Envelope(
            data={"consent": response, "capture": None, "invalidated_refs": []},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/meetings/{meeting_id}/capture/start", status_code=status.HTTP_202_ACCEPTED)
async def start_capture(
    meeting_id: UUID,
    request: StartCaptureRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-037: Start capture with accepted consent."""
    try:
        client_id = uuid4()  # Mock
        capture_service = CaptureService(db)
        
        capture_id = uuid4()
        capture = await capture_service.start_capture(
            tenant_id=MOCK_TENANT,
            client_id=client_id,
            meeting_id=meeting_id,
            consent_id=request.consent_id,
            provider_key="test-provider",
            actor=MOCK_ACTOR,
        )
        capture.id = capture_id
        
        await db.commit()
        
        response = CaptureResponse(
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
        
        return Envelope(
            data={"capture": response},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/meetings/{meeting_id}/capture/segments")
async def append_segments(
    meeting_id: UUID,
    request: AppendSegmentRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """Append segment progress (audio_ms, transcript_ms).
    
    Append-only: never decreases positions.
    """
    try:
        # Get active capture for meeting (simplified)
        client_id = uuid4()
        capture_service = CaptureService(db)
        
        # Mock: would query active capture by meeting_id
        capture_id = uuid4()
        
        capture = await capture_service.append_segment_progress(
            tenant_id=MOCK_TENANT,
            client_id=client_id,
            capture_id=capture_id,
            audio_ms=request.audio_ms,
            transcript_ms=request.transcript_ms,
        )
        
        await db.commit()
        
        response = CaptureResponse(
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
        
        return Envelope(
            data={"capture": response},
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/extractions/{extraction_id}/edits", status_code=status.HTTP_201_CREATED)
async def apply_extraction_edits(
    extraction_id: UUID,
    request: ExtractionEditRequest,
    db: AsyncSession = Depends(get_db),
) -> Envelope[dict]:
    """API-044: Apply RM corrections to extraction.
    
    Creates immutable new revision with RM_ENTERED origin.
    Preserves original evidence, adds correction reason.
    """
    try:
        client_id = uuid4()  # Mock
        extraction_service = ExtractionService(db)
        
        # Mock: would fetch current artifact revision
        artifact_id = extraction_id
        current_revision_id = uuid4()
        
        new_revision = await extraction_service.apply_extraction_edits(
            tenant_id=MOCK_TENANT,
            client_id=client_id,
            artifact_id=artifact_id,
            current_revision_id=current_revision_id,
            edits=request.edits,
            suppressed_item_keys=request.suppressed_item_keys,
            actor=MOCK_ACTOR,
        )
        
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
                "invalidated_refs": [],  # Would list downstream dependencies
            },
            meta=ResponseMeta(request_id=uuid4(), served_at=datetime.utcnow())
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
