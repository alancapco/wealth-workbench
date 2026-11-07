"""Message provider adapter stub - returns UNCONFIGURED without DEC-02."""
from typing import Literal
from uuid import UUID, uuid4

from app.schemas.message import Message, MessageChannel


ProviderState = Literal["ACCEPTED", "SCHEDULED", "DELIVERED", "NOT_ACCEPTED", "UNKNOWN"]


class MessageProviderReceipt:
    """Receipt from message provider."""
    
    def __init__(
        self,
        receipt_id: str,
        provider_key: str,
        provider_ref: str | None,
        status: ProviderState,
        error_code: str | None = None,
    ):
        self.receipt_id = receipt_id
        self.provider_key = provider_key
        self.provider_ref = provider_ref
        self.status = status
        self.error_code = error_code


class MessageProviderStub:
    """
    Stub message provider - returns UNCONFIGURED without DEC-02 provider config.
    
    Real implementation would:
    - Check for approved DEC-02 integration config
    - Load provider credentials
    - Call external email/SMS/WhatsApp APIs
    - Handle provider-specific error codes
    - Support idempotency and readback
    """

    def __init__(self, provider_config: dict | None = None):
        self.provider_config = provider_config

    async def send_message(
        self,
        message: Message,
        recipient_destination: str,
        tenant_id: str,
        client_id: UUID,
    ) -> MessageProviderReceipt:
        """
        Send message via provider.
        
        Returns UNCONFIGURED if no provider configured (fail-closed).
        Real implementation would validate DNC, channel opt-out, and disclosure.
        """
        # Fail-closed: no provider config = UNCONFIGURED
        if not self.provider_config:
            return MessageProviderReceipt(
                receipt_id=str(uuid4()),
                provider_key="UNCONFIGURED",
                provider_ref=None,
                status="NOT_ACCEPTED",
                error_code="PROVIDER_UNCONFIGURED",
            )

        # Check for recipient confirmation
        recipient = next(
            (r for r in message.recipients if r.destination == recipient_destination),
            None
        )
        if not recipient:
            return MessageProviderReceipt(
                receipt_id=str(uuid4()),
                provider_key=self.provider_config.get("provider_key", "test-provider"),
                provider_ref=None,
                status="NOT_ACCEPTED",
                error_code="RECIPIENT_NOT_FOUND",
            )

        if not recipient.confirmed:
            return MessageProviderReceipt(
                receipt_id=str(uuid4()),
                provider_key=self.provider_config.get("provider_key", "test-provider"),
                provider_ref=None,
                status="NOT_ACCEPTED",
                error_code="RECIPIENT_NOT_CONFIRMED",
            )

        # Stub: simulate successful send for testing
        # Real implementation would call provider API here
        return MessageProviderReceipt(
            receipt_id=str(uuid4()),
            provider_key=self.provider_config.get("provider_key", "test-provider"),
            provider_ref=f"msg-{uuid4()}",
            status="ACCEPTED",
            error_code=None,
        )

    async def check_dnc(
        self, destination: str, channel: MessageChannel, tenant_id: str
    ) -> bool:
        """
        Check if destination is on Do Not Contact list for channel.
        
        Returns True if blocked.
        Real implementation would check DNC registry.
        """
        # Stub: no DNC checks without config
        if not self.provider_config:
            # Fail safe: block if we can't verify
            return True
        
        # Stub: allow all for testing
        return False

    async def check_channel_opt_out(
        self, destination: str, channel: MessageChannel, tenant_id: str
    ) -> bool:
        """
        Check if destination has opted out of channel.
        
        Returns True if opted out.
        Real implementation would check opt-out registry.
        """
        # Stub: no opt-out checks without config
        if not self.provider_config:
            # Fail safe: block if we can't verify
            return True
        
        # Stub: allow all for testing
        return False

    async def readback_status(
        self, provider_ref: str, provider_key: str
    ) -> MessageProviderReceipt:
        """
        Read back current status from provider.
        
        Used for reconciliation after timeout/UNKNOWN.
        Real implementation would query provider status API.
        """
        if not self.provider_config:
            return MessageProviderReceipt(
                receipt_id=str(uuid4()),
                provider_key="UNCONFIGURED",
                provider_ref=provider_ref,
                status="UNKNOWN",
                error_code="PROVIDER_UNCONFIGURED",
            )

        # Stub: simulate successful readback
        return MessageProviderReceipt(
            receipt_id=str(uuid4()),
            provider_key=provider_key,
            provider_ref=provider_ref,
            status="DELIVERED",
            error_code=None,
        )
