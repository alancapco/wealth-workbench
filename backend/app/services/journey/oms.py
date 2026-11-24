"""Sandbox OMS dispatcher. Marks claimed outbox actions succeeded.

The receipt is labelled as a demo sink. It never calls a live broker.
"""
import hashlib
from uuid import uuid4

from app.services.actions.outbox_worker import OutboxWorker
from app.models.action import OutboxAction


async def sandbox_oms_dispatcher(worker: OutboxWorker, action: OutboxAction) -> None:
    lease = action.lease_token or uuid4()
    request_hash = hashlib.sha256(str(action.id).encode()).hexdigest()
    receipt = f"sandbox-oms:{action.id}"
    # The first claim records a DISPATCH attempt. A later claim of the same
    # action (lease expired while SENDING) must not insert that attempt again.
    if not action.attempt_count:
        await worker.record_dispatch_started(action, lease, request_hash)
    await worker.record_readback_attempt(
        action, lease, request_hash, "CONFIRMED", receipt_ref=receipt,
    )
