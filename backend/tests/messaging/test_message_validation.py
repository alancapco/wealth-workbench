"""
U-011 Message Service Unit Tests

Simplified tests focusing on message service logic without full DB schema.
Tests the core message generation and validation logic.
"""
import json
from uuid import UUID, uuid4

import pytest

from app.schemas.message import MessageGenerate, MessageRecipient, Message
from app.schemas.common import ConfigRef, ItemRef
from app.services.messaging.provider_stub import MessageProviderStub


class TestMessageValidation:
    """Test message generation validation rules."""

    def test_followup_requires_accepted_items(self):
        """FOLLOWUP messages must have accepted_item_refs."""
        with pytest.raises(ValueError):
            MessageGenerate(
                mode="FOLLOWUP",
                channel="EMAIL",
                template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
                accepted_item_refs=[],  # Empty - validation should fail
                priority_reason_ref=None,
            ).model_post_init(None)

    def test_message_mode_validation(self):
        """Message mode must be FOLLOWUP or OUTREACH."""
        # Valid modes
        msg1 = MessageGenerate(
            mode="FOLLOWUP",
            channel="EMAIL",
            template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
            accepted_item_refs=[
                ItemRef(
                    artifact_ref=ConfigRef(id=uuid4(), revision=1, hash="b" * 64),
                    item_key="test",
                    item_hash="c" * 64,
                )
            ],
        )
        assert msg1.mode == "FOLLOWUP"

        msg2 = MessageGenerate(
            mode="OUTREACH",
            channel="EMAIL",
            template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
            accepted_item_refs=[],
            priority_reason_ref=None,  # Will be added by service
        )
        assert msg2.mode == "OUTREACH"

    def test_message_channel_validation(self):
        """Message channel must be EMAIL, SMS, or WHATSAPP."""
        for channel in ["EMAIL", "SMS", "WHATSAPP"]:
            msg = MessageGenerate(
                mode="FOLLOWUP",
                channel=channel,
                template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
                accepted_item_refs=[
                    ItemRef(
                        artifact_ref=ConfigRef(id=uuid4(), revision=1, hash="b" * 64),
                        item_key="test",
                        item_hash="c" * 64,
                    )
                ],
            )
            assert msg.channel == channel


class TestMessageRecipients:
    """Test recipient confirmation logic."""

    def test_recipients_start_unconfirmed(self):
        """Recipients should start with confirmed=False."""
        recipient = MessageRecipient(
            contact_id="contact-123",
            destination="test@example.com",
            confirmed=False,
        )
        assert recipient.confirmed == False

    def test_recipient_confirmation_required_for_send(self):
        """Provider blocks unconfirmed recipients."""
        provider = MessageProviderStub(provider_config={"provider_key": "test"})
        
        message = Message(
            mode="FOLLOWUP",
            channel="EMAIL",
            template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
            recipients=[
                MessageRecipient(
                    contact_id="contact-1",
                    destination="test@example.com",
                    confirmed=False,  # Not confirmed
                )
            ],
            subject="Test",
            body="Test body",
            disclosures=[],
            basis_refs=[],
            priority_reason_ref=None,
            claims=[],
        )
        
        # Synchronous wrapper for async test
        import asyncio
        receipt = asyncio.run(provider.send_message(
            message=message,
            recipient_destination="test@example.com",
            tenant_id="test-tenant",
            client_id=uuid4(),
        ))
        
        assert receipt.status == "NOT_ACCEPTED"
        assert receipt.error_code == "RECIPIENT_NOT_CONFIRMED"


class TestProviderStub:
    """Test message provider stub behavior."""

    @pytest.mark.asyncio
    async def test_provider_unconfigured_returns_error(self):
        """Provider without config returns UNCONFIGURED (fail-closed)."""
        provider = MessageProviderStub(provider_config=None)
        
        message = Message(
            mode="FOLLOWUP",
            channel="EMAIL",
            template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
            recipients=[
                MessageRecipient(
                    contact_id="contact-1",
                    destination="test@example.com",
                    confirmed=True,
                )
            ],
            subject="Test",
            body="Test body",
            disclosures=[],
            basis_refs=[],
            priority_reason_ref=None,
            claims=[],
        )
        
        receipt = await provider.send_message(
            message=message,
            recipient_destination="test@example.com",
            tenant_id="test-tenant",
            client_id=uuid4(),
        )
        
        assert receipt.status == "NOT_ACCEPTED"
        assert receipt.error_code == "PROVIDER_UNCONFIGURED"
        assert receipt.provider_key == "UNCONFIGURED"

    @pytest.mark.asyncio
    async def test_provider_accepts_confirmed_recipient(self):
        """Provider accepts message with confirmed recipient."""
        provider = MessageProviderStub(provider_config={"provider_key": "test-provider"})
        
        message = Message(
            mode="FOLLOWUP",
            channel="EMAIL",
            template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
            recipients=[
                MessageRecipient(
                    contact_id="contact-1",
                    destination="test@example.com",
                    confirmed=True,  # Confirmed
                )
            ],
            subject="Test",
            body="Test body",
            disclosures=[],
            basis_refs=[],
            priority_reason_ref=None,
            claims=[],
        )
        
        receipt = await provider.send_message(
            message=message,
            recipient_destination="test@example.com",
            tenant_id="test-tenant",
            client_id=uuid4(),
        )
        
        assert receipt.status == "ACCEPTED"
        assert receipt.error_code is None
        assert receipt.provider_ref is not None

    @pytest.mark.asyncio
    async def test_dnc_check_fails_safe_without_config(self):
        """DNC check blocks if provider unconfigured (fail-safe)."""
        provider = MessageProviderStub(provider_config=None)
        
        is_blocked = await provider.check_dnc(
            destination="test@example.com",
            channel="EMAIL",
            tenant_id="test-tenant",
        )
        
        # Fail-safe: block if we can't verify
        assert is_blocked == True

    @pytest.mark.asyncio
    async def test_channel_opt_out_fails_safe_without_config(self):
        """Channel opt-out check blocks if provider unconfigured (fail-safe)."""
        provider = MessageProviderStub(provider_config=None)
        
        is_opted_out = await provider.check_channel_opt_out(
            destination="test@example.com",
            channel="EMAIL",
            tenant_id="test-tenant",
        )
        
        # Fail-safe: block if we can't verify
        assert is_opted_out == True

    @pytest.mark.asyncio
    async def test_readback_returns_unknown_without_config(self):
        """Readback returns UNKNOWN if provider unconfigured."""
        provider = MessageProviderStub(provider_config=None)
        
        receipt = await provider.readback_status(
            provider_ref="msg-123",
            provider_key="test-provider",
        )
        
        assert receipt.status == "UNKNOWN"
        assert receipt.error_code == "PROVIDER_UNCONFIGURED"


class TestMessageArtifactStructure:
    """Test message artifact payload structure."""

    def test_message_has_required_fields(self):
        """Message artifact has all required fields."""
        message = Message(
            mode="FOLLOWUP",
            channel="EMAIL",
            template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
            recipients=[
                MessageRecipient(
                    contact_id="contact-1",
                    destination="test@example.com",
                    confirmed=True,
                )
            ],
            subject="Test Subject",
            body="Test body content",
            disclosures=[],
            basis_refs=[
                ItemRef(
                    artifact_ref=ConfigRef(id=uuid4(), revision=1, hash="b" * 64),
                    item_key="note_1",
                    item_hash="c" * 64,
                )
            ],
            priority_reason_ref=None,
            claims=[],
        )
        
        # Verify structure
        assert message.mode == "FOLLOWUP"
        assert message.channel == "EMAIL"
        assert message.subject == "Test Subject"
        assert len(message.recipients) == 1
        assert len(message.basis_refs) == 1

    def test_sms_message_has_no_subject(self):
        """SMS messages should not have subject."""
        message = Message(
            mode="OUTREACH",
            channel="SMS",
            template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
            recipients=[
                MessageRecipient(
                    contact_id="contact-1",
                    destination="+1234567890",
                    confirmed=True,
                )
            ],
            subject=None,  # SMS has no subject
            body="Test SMS body",
            disclosures=[],
            basis_refs=[],
            priority_reason_ref=None,
            claims=[],
        )
        
        assert message.subject is None
        assert message.channel == "SMS"

    def test_message_serialization(self):
        """Message can be serialized to JSON and back."""
        original = Message(
            mode="FOLLOWUP",
            channel="EMAIL",
            template_ref=ConfigRef(id=uuid4(), revision=1, hash="a" * 64),
            recipients=[
                MessageRecipient(
                    contact_id="contact-1",
                    destination="test@example.com",
                    confirmed=True,
                )
            ],
            subject="Test",
            body="Body",
            disclosures=[],
            basis_refs=[],
            priority_reason_ref=None,
            claims=[],
        )
        
        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = Message.model_validate_json(json_str)
        
        assert restored.mode == original.mode
        assert restored.channel == original.channel
        assert restored.subject == original.subject
        assert len(restored.recipients) == len(original.recipients)
