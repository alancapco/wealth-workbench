"""Message provider adapter — TEST DOUBLE.

``send_message`` and ``readback_status`` simulate a provider for the U-011 unit
tests. They MUST NOT be called from production code: no real provider is wired
into the outbox, and a simulated ACCEPTED/DELIVERED receipt would be a false
record of client contact.

``check_dnc`` / ``check_channel_opt_out`` are fail-closed guards over the
approved consent registry (``configuration_revisions``, CONSENT class, APPROVED
status, config_key ``contact_policy_registry``). Its JSON value has the shape::

    {"dnc": {"EMAIL:client@example.com": "CLEARED"},
     "opt_outs": {"EMAIL:client@example.com": "CLEARED"}}

A contact point is allowed only when an approved row explicitly records it as
CLEARED. Any missing, retired, malformed or unverifiable state is blocked.
"""
import json
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.admin import ConfigurationRevision
from app.schemas.message import Message, MessageChannel


ProviderState = Literal["ACCEPTED", "SCHEDULED", "DELIVERED", "NOT_ACCEPTED", "UNKNOWN"]

REGISTRY_CONFIG_KEY = "contact_policy_registry"
REGISTRY_CLEARED = "CLEARED"


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
    """Test double: simulated dispatch plus fail-closed consent-registry guards."""

    def __init__(
        self,
        provider_config: dict | None = None,
        session: AsyncSession | None = None,
    ):
        self.provider_config = provider_config
        self.session = session

    @staticmethod
    def _assert_test_context() -> None:
        # Simulated receipts must never become production evidence of a client send.
        if settings.APP_ENV.lower() == "production":
            raise RuntimeError(
                "MessageProviderStub is a test double and must not be used in production"
            )

    async def _registry_state(
        self, tenant_id: str, destination: str, channel: MessageChannel, kind: str
    ) -> str:
        """Read the approved registry decision; UNVERIFIED when it cannot be proven."""
        if self.session is None:
            return "UNVERIFIED"
        try:
            stmt = (
                select(ConfigurationRevision.value)
                .where(
                    ConfigurationRevision.tenant_id == tenant_id,
                    ConfigurationRevision.config_class == "CONSENT",
                    ConfigurationRevision.config_key == REGISTRY_CONFIG_KEY,
                    ConfigurationRevision.status == "APPROVED",
                )
                .order_by(ConfigurationRevision.revision.desc())
                .limit(1)
            )
            value = (await self.session.execute(stmt)).scalar_one_or_none()
            if value is None:
                return "UNVERIFIED"
            registry = json.loads(value)
            return str(
                registry.get(kind, {}).get(f"{channel}:{destination}", "UNVERIFIED")
            )
        except Exception:
            # Fail closed: a lookup failure is indistinguishable from a blocked contact.
            return "UNVERIFIED"

    async def send_message(
        self,
        message: Message,
        recipient_destination: str,
        tenant_id: str,
        client_id: UUID,
    ) -> MessageProviderReceipt:
        """Simulate a provider send (test double only)."""
        self._assert_test_context()

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

        # Simulated acceptance for tests; no external API is called here.
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
        """Return True if blocked. Only an explicit approved CLEARED row allows contact."""
        return await self._registry_state(tenant_id, destination, channel, "dnc") != REGISTRY_CLEARED

    async def check_channel_opt_out(
        self, destination: str, channel: MessageChannel, tenant_id: str
    ) -> bool:
        """Return True if opted out. Only an explicit approved CLEARED row allows contact."""
        return await self._registry_state(tenant_id, destination, channel, "opt_outs") != REGISTRY_CLEARED

    async def readback_status(
        self, provider_ref: str, provider_key: str
    ) -> MessageProviderReceipt:
        """Simulate provider readback (test double only)."""
        self._assert_test_context()

        if not self.provider_config:
            return MessageProviderReceipt(
                receipt_id=str(uuid4()),
                provider_key="UNCONFIGURED",
                provider_ref=provider_ref,
                status="UNKNOWN",
                error_code="PROVIDER_UNCONFIGURED",
            )

        # Simulated readback for tests; not a real provider status query.
        return MessageProviderReceipt(
            receipt_id=str(uuid4()),
            provider_key=provider_key,
            provider_ref=provider_ref,
            status="DELIVERED",
            error_code=None,
        )
