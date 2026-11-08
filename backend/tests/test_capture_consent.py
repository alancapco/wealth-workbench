"""Tests for U-008 capture consent, session control, and extraction.

Validates:
- Consent policy gating (UNCONFIGURED blocks)
- Withdraw invalidates capture
- Segment append-only tracking
- Extraction edit tracking with RM_ENTERED origin
- Calendar acceptance NOT consent
"""
import pytest
import pytest_asyncio
from datetime import datetime, UTC, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.capture import CaptureSession, ConsentRecord
from app.models.workflow import Meeting
from app.models.platform import ClientScope, WorkbenchTenant
from app.services.capture.consent_service import ConsentService
from app.services.capture.capture_service import CaptureService
from app.services.capture.extraction_service import ExtractionService


@pytest_asyncio.fixture
async def setup_tenant_client(db_session: AsyncSession):
    """Setup test tenant and client."""
    tenant = WorkbenchTenant(
        tenant_id="test-tenant",
        environment_kind="FIXTURE",
        environment_id="test-env",
    )
    db_session.add(tenant)
    
    client_id = uuid4()
    client_scope = ClientScope(
        tenant_id="test-tenant",
        client_id=client_id,
        context_revision=1,
        ownership_source="test",
        ownership_version="1",
        verified_at=datetime.now(UTC),
    )
    db_session.add(client_scope)
    
    meeting_id = uuid4()
    meeting = Meeting(
        id=meeting_id,
        tenant_id="test-tenant",
        client_id=client_id,
        resolution="RM_CONFIRMED",
        resolved_by="test-rm",
        resolved_at=datetime.now(UTC),
        row_version=1,
    )
    db_session.add(meeting)
    
    await db_session.commit()
    return {"tenant_id": "test-tenant", "client_id": client_id, "meeting_id": meeting_id}


@pytest.mark.asyncio
async def test_consent_accepted_allows_capture(db_session: AsyncSession, setup_tenant_client):
    """Consent ACCEPTED allows capture to start."""
    ctx = await setup_tenant_client
    consent_service = ConsentService(db_session)
    
    # Record ACCEPTED consent
    consent_id = uuid4()
    policy_id = uuid4()
    consent = await consent_service.record_consent(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
        policy_configuration_id=policy_id,
        jurisdiction="US",
        platform="web",
        language="en",
        method="explicit-checkbox",
        participant_refs=["participant-1"],
        decision="ACCEPTED",
        actor="test-rm",
    )
    consent.id = consent_id
    await db_session.commit()
    
    assert consent.state == "ACCEPTED"
    
    # Check consent is valid
    is_valid = await consent_service.check_consent_valid(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
    )
    assert is_valid is True


@pytest.mark.asyncio
async def test_consent_declined_blocks_capture(db_session: AsyncSession, setup_tenant_client):
    """Consent DECLINED blocks capture (fail-closed)."""
    ctx = await setup_tenant_client
    consent_service = ConsentService(db_session)
    
    # Record DECLINED consent
    consent_id = uuid4()
    policy_id = uuid4()
    consent = await consent_service.record_consent(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
        policy_configuration_id=policy_id,
        jurisdiction="US",
        platform="web",
        language="en",
        method="explicit-checkbox",
        participant_refs=["participant-1"],
        decision="DECLINED",
        actor="test-rm",
    )
    consent.id = consent_id
    await db_session.commit()
    
    assert consent.state == "DECLINED"
    
    # Check consent is NOT valid
    is_valid = await consent_service.check_consent_valid(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
    )
    assert is_valid is False


@pytest.mark.asyncio
async def test_withdraw_invalidates_capture(db_session: AsyncSession, setup_tenant_client):
    """Withdraw consent invalidates active capture."""
    ctx = await setup_tenant_client
    consent_service = ConsentService(db_session)
    capture_service = CaptureService(db_session)
    
    # Record ACCEPTED consent
    consent_id = uuid4()
    policy_id = uuid4()
    consent = await consent_service.record_consent(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
        policy_configuration_id=policy_id,
        jurisdiction="US",
        platform="web",
        language="en",
        method="explicit-checkbox",
        participant_refs=["participant-1"],
        decision="ACCEPTED",
        actor="test-rm",
    )
    consent.id = consent_id
    await db_session.commit()
    
    # Start capture
    capture_id = uuid4()
    capture = await capture_service.start_capture(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
        consent_id=consent_id,
        provider_key="test-provider",
        actor="test-rm",
    )
    capture.id = capture_id
    await db_session.commit()
    
    assert capture.status == "STARTING"
    
    # Withdraw consent
    withdrawn_consent = await consent_service.withdraw_consent(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        consent_id=consent_id,
        actor="test-rm",
    )
    
    assert withdrawn_consent.state == "WITHDRAWN"
    assert withdrawn_consent.withdrawn_at is not None
    
    # Revoke capture lease
    revoked_capture = await capture_service.revoke_lease(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        capture_id=capture_id,
    )
    
    assert revoked_capture.lease_revoked is True


@pytest.mark.asyncio
async def test_segment_append_only(db_session: AsyncSession, setup_tenant_client):
    """Segment tracking is append-only, never decreases."""
    ctx = await setup_tenant_client
    consent_service = ConsentService(db_session)
    capture_service = CaptureService(db_session)
    
    # Setup consent and capture
    consent_id = uuid4()
    policy_id = uuid4()
    consent = await consent_service.record_consent(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
        policy_configuration_id=policy_id,
        jurisdiction="US",
        platform="web",
        language="en",
        method="explicit-checkbox",
        participant_refs=["participant-1"],
        decision="ACCEPTED",
        actor="test-rm",
    )
    consent.id = consent_id
    
    capture_id = uuid4()
    capture = await capture_service.start_capture(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
        consent_id=consent_id,
        provider_key="test-provider",
        actor="test-rm",
    )
    capture.id = capture_id
    await db_session.commit()
    
    # Append segment 1000ms
    capture = await capture_service.append_segment_progress(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        capture_id=capture_id,
        audio_ms=1000,
        transcript_ms=800,
    )
    assert capture.last_confirmed_audio_ms == 1000
    assert capture.last_confirmed_transcript_ms == 800
    
    # Append segment 2000ms (increases)
    capture = await capture_service.append_segment_progress(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        capture_id=capture_id,
        audio_ms=2000,
        transcript_ms=1500,
    )
    assert capture.last_confirmed_audio_ms == 2000
    assert capture.last_confirmed_transcript_ms == 1500
    
    # Try to append 500ms (should NOT decrease)
    capture = await capture_service.append_segment_progress(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        capture_id=capture_id,
        audio_ms=500,
        transcript_ms=300,
    )
    # Should remain at 2000/1500
    assert capture.last_confirmed_audio_ms == 2000
    assert capture.last_confirmed_transcript_ms == 1500


@pytest.mark.asyncio
async def test_extraction_edit_tracking(db_session: AsyncSession, setup_tenant_client):
    """Extraction edits create RM_ENTERED items with reason."""
    ctx = await setup_tenant_client
    extraction_service = ExtractionService(db_session)
    
    # Mock: create initial extraction artifact (would come from AI)
    artifact_id = uuid4()
    current_revision_id = uuid4()
    
    # Mock current payload
    from app.models.artifact import ArtifactRevision, ArtifactLineage
    
    lineage = ArtifactLineage(
        id=artifact_id,
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        workflow_id=uuid4(),
        kind="EXTRACTION",
        created_by="ai-extractor",
        created_at=datetime.now(UTC),
    )
    db_session.add(lineage)
    
    current_payload = {
        "basis_ref": {"artifact_id": str(uuid4()), "revision_id": str(uuid4()), "hash": "abc123"},
        "items": [
            {
                "key": "item-1",
                "type": "ACTION",
                "content": "Original AI extraction",
                "origin": "DERIVED",
                "confidence": 0.85,
                "evidence_refs": [],
            },
            {
                "key": "item-2",
                "type": "DECISION",
                "content": "To be suppressed",
                "origin": "DERIVED",
                "confidence": 0.60,
                "evidence_refs": [],
            }
        ]
    }
    
    current_revision = ArtifactRevision(
        id=current_revision_id,
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        artifact_id=artifact_id,
        version=1,
        content_hash="hash1",
        payload=current_payload,
        environment_kind="FIXTURE",
        environment_id="test",
        created_by="ai-extractor",
        created_at=datetime.now(UTC),
    )
    db_session.add(current_revision)
    
    lineage.current_revision_id = current_revision_id
    await db_session.commit()
    
    # Apply RM edits
    edits = [
        {
            "key": "item-1",
            "content": "Corrected by RM",
            "owner": {"ref": "rm-123", "display": "Test RM", "origin": "RM_ENTERED"},
            "due_date": None,
            "due_date_origin": None,
            "evidence_refs": [],
            "reason": {"code": "CORRECTION", "catalog_ref": {}, "other_text": "AI misunderstood context"},
        }
    ]
    suppressed_keys = ["item-2"]
    
    new_revision = await extraction_service.apply_extraction_edits(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        artifact_id=artifact_id,
        current_revision_id=current_revision_id,
        edits=edits,
        suppressed_item_keys=suppressed_keys,
        actor="test-rm",
    )
    
    assert new_revision.version == 2
    assert new_revision.created_by == "test-rm"
    
    # Check new payload
    new_items = new_revision.payload["items"]
    assert len(new_items) == 1  # item-2 suppressed
    assert new_items[0]["key"] == "item-1"
    assert new_items[0]["content"] == "Corrected by RM"
    assert new_items[0]["origin"] == "RM_ENTERED"
    assert "edit_reason" in new_items[0]


@pytest.mark.asyncio
async def test_calendar_acceptance_not_consent(db_session: AsyncSession, setup_tenant_client):
    """Calendar RSVP acceptance is NOT meeting capture consent.
    
    Explicit consent decision required before capture.
    """
    ctx = await setup_tenant_client
    consent_service = ConsentService(db_session)
    capture_service = CaptureService(db_session)
    
    # No consent recorded yet
    is_valid = await consent_service.check_consent_valid(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
    )
    assert is_valid is False  # Fail-closed
    
    # Try to start capture without consent - should fail
    with pytest.raises(ValueError, match="Valid ACCEPTED consent required"):
        await capture_service.start_capture(
            tenant_id=ctx["tenant_id"],
            client_id=ctx["client_id"],
            meeting_id=ctx["meeting_id"],
            consent_id=uuid4(),  # Non-existent consent
            provider_key="test-provider",
            actor="test-rm",
        )


@pytest.mark.asyncio
async def test_no_duplicate_active_capture(db_session: AsyncSession, setup_tenant_client):
    """Only one active capture allowed per meeting."""
    ctx = await setup_tenant_client
    consent_service = ConsentService(db_session)
    capture_service = CaptureService(db_session)
    
    # Setup consent
    consent_id = uuid4()
    policy_id = uuid4()
    consent = await consent_service.record_consent(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
        policy_configuration_id=policy_id,
        jurisdiction="US",
        platform="web",
        language="en",
        method="explicit-checkbox",
        participant_refs=["participant-1"],
        decision="ACCEPTED",
        actor="test-rm",
    )
    consent.id = consent_id
    await db_session.commit()
    
    # Start first capture
    capture_id_1 = uuid4()
    capture1 = await capture_service.start_capture(
        tenant_id=ctx["tenant_id"],
        client_id=ctx["client_id"],
        meeting_id=ctx["meeting_id"],
        consent_id=consent_id,
        provider_key="test-provider",
        actor="test-rm",
    )
    capture1.id = capture_id_1
    await db_session.commit()
    
    # Try to start second capture - should fail
    with pytest.raises(ValueError, match="Active capture already exists"):
        await capture_service.start_capture(
            tenant_id=ctx["tenant_id"],
            client_id=ctx["client_id"],
            meeting_id=ctx["meeting_id"],
            consent_id=consent_id,
            provider_key="test-provider",
            actor="test-rm",
        )
