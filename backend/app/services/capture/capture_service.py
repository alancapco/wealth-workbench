"""Capture session management: start, pause, resume, stop with segment tracking."""
from datetime import datetime, UTC, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.capture import CaptureSession, ConsentRecord


class CaptureService:
    """Manage capture session lifecycle with lease and segment append tracking."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_capture(
        self,
        tenant_id: str,
        client_id: UUID,
        meeting_id: UUID,
        consent_id: UUID,
        provider_key: str,
        actor: str,
    ) -> CaptureSession:
        """Start capture session with approved consent and lease.
        
        Caller must verify:
        - Current consent is ACCEPTED
        - Policy allows capture
        - Device/provider available
        """
        # Check consent is ACCEPTED
        consent_stmt = select(ConsentRecord).where(
            ConsentRecord.tenant_id == tenant_id,
            ConsentRecord.client_id == client_id,
            ConsentRecord.id == consent_id,
        )
        consent_result = await self.session.execute(consent_stmt)
        consent = consent_result.scalar_one_or_none()
        
        if not consent or consent.state != "ACCEPTED":
            raise ValueError("Valid ACCEPTED consent required to start capture")
        
        # Check no active capture for this meeting
        active_stmt = select(CaptureSession).where(
            CaptureSession.tenant_id == tenant_id,
            CaptureSession.meeting_id == meeting_id,
            CaptureSession.status.in_(["STARTING", "RECORDING", "PAUSED", "STOPPING"]),
        )
        active_result = await self.session.execute(active_stmt)
        if active_result.scalar_one_or_none():
            raise ValueError("Active capture already exists for this meeting")
        
        # Create new session with lease
        capture = CaptureSession(
            id=uuid4(),
            tenant_id=tenant_id,
            client_id=client_id,
            meeting_id=meeting_id,
            consent_id=consent_id,
            provider_key=provider_key,
            status="STARTING",
            row_version=1,
            lease_valid_until=datetime.now(UTC) + timedelta(hours=4),  # Policy-driven
            lease_revoked=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        
        self.session.add(capture)
        await self.session.flush()
        return capture

    async def update_status(
        self,
        tenant_id: str,
        client_id: UUID,
        capture_id: UUID,
        new_status: str,
        provider_ref: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> CaptureSession:
        """Update capture status (STARTING->RECORDING->PAUSED->STOPPED->COMPLETE/FAILED)."""
        stmt = select(CaptureSession).where(
            CaptureSession.tenant_id == tenant_id,
            CaptureSession.client_id == client_id,
            CaptureSession.id == capture_id,
        )
        result = await self.session.execute(stmt)
        capture = result.scalar_one_or_none()
        
        if not capture:
            raise ValueError(f"Capture {capture_id} not found")
        
        capture.status = new_status
        capture.row_version += 1
        capture.updated_at = datetime.now(UTC)
        
        if provider_ref:
            capture.provider_ref = provider_ref
        if error_code:
            capture.error_code = error_code
        
        await self.session.flush()
        return capture

    async def pause_capture(
        self,
        tenant_id: str,
        client_id: UUID,
        capture_id: UUID,
    ) -> CaptureSession:
        """Pause active recording."""
        return await self.update_status(tenant_id, client_id, capture_id, "PAUSED")

    async def resume_capture(
        self,
        tenant_id: str,
        client_id: UUID,
        capture_id: UUID,
    ) -> CaptureSession:
        """Resume from PAUSED to RECORDING.
        
        Caller must recheck current policy before resuming.
        """
        stmt = select(CaptureSession).where(
            CaptureSession.tenant_id == tenant_id,
            CaptureSession.client_id == client_id,
            CaptureSession.id == capture_id,
        )
        result = await self.session.execute(stmt)
        capture = result.scalar_one_or_none()
        
        if not capture:
            raise ValueError(f"Capture {capture_id} not found")
        
        if capture.status != "PAUSED":
            raise ValueError(f"Can only resume from PAUSED, current: {capture.status}")
        
        # Check lease still valid
        if capture.lease_revoked or (capture.lease_valid_until and capture.lease_valid_until < datetime.now(UTC)):
            raise ValueError("Capture lease expired or revoked")
        
        return await self.update_status(tenant_id, client_id, capture_id, "RECORDING")

    async def stop_capture(
        self,
        tenant_id: str,
        client_id: UUID,
        capture_id: UUID,
    ) -> CaptureSession:
        """Stop capture session."""
        return await self.update_status(tenant_id, client_id, capture_id, "STOPPING")

    async def append_segment_progress(
        self,
        tenant_id: str,
        client_id: UUID,
        capture_id: UUID,
        audio_ms: Optional[int] = None,
        transcript_ms: Optional[int] = None,
    ) -> CaptureSession:
        """Append-only segment tracking: last confirmed positions.
        
        Never decreases; preserves progress across outage/restart.
        """
        stmt = select(CaptureSession).where(
            CaptureSession.tenant_id == tenant_id,
            CaptureSession.client_id == client_id,
            CaptureSession.id == capture_id,
        )
        result = await self.session.execute(stmt)
        capture = result.scalar_one_or_none()
        
        if not capture:
            raise ValueError(f"Capture {capture_id} not found")
        
        if audio_ms is not None:
            if capture.last_confirmed_audio_ms is None or audio_ms > capture.last_confirmed_audio_ms:
                capture.last_confirmed_audio_ms = audio_ms
        
        if transcript_ms is not None:
            if capture.last_confirmed_transcript_ms is None or transcript_ms > capture.last_confirmed_transcript_ms:
                capture.last_confirmed_transcript_ms = transcript_ms
        
        capture.updated_at = datetime.now(UTC)
        await self.session.flush()
        return capture

    async def revoke_lease(
        self,
        tenant_id: str,
        client_id: UUID,
        capture_id: UUID,
    ) -> CaptureSession:
        """Revoke capture lease (on consent withdrawal)."""
        stmt = select(CaptureSession).where(
            CaptureSession.tenant_id == tenant_id,
            CaptureSession.client_id == client_id,
            CaptureSession.id == capture_id,
        )
        result = await self.session.execute(stmt)
        capture = result.scalar_one_or_none()
        
        if not capture:
            raise ValueError(f"Capture {capture_id} not found")
        
        capture.lease_revoked = True
        capture.updated_at = datetime.now(UTC)
        await self.session.flush()
        return capture

    async def get_capture(
        self,
        tenant_id: str,
        client_id: UUID,
        capture_id: UUID,
    ) -> Optional[CaptureSession]:
        """Retrieve capture session by ID."""
        stmt = select(CaptureSession).where(
            CaptureSession.tenant_id == tenant_id,
            CaptureSession.client_id == client_id,
            CaptureSession.id == capture_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
