"""Message generation service."""
import hashlib
import json
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ArtifactLineage, ArtifactRevision
from app.schemas.message import MessageGenerate, Message, MessageRecipient, MessageDisclosure, MessageClaim
from app.schemas.common import Origin, EvidenceRef


class MessageService:
    """
    Message generation creates Message artifacts from accepted items or priority reasons.
    
    Messages are grounded in accepted meeting items (FOLLOWUP) or priority reasons (OUTREACH).
    No unsupported claims - missing facts are omitted, not fabricated.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def _compute_hash(self, data: dict) -> str:
        """Compute SHA-256 hash of canonical JSON."""
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    async def generate_message(
        self,
        tenant_id: str,
        client_id: UUID,
        workflow_id: UUID,
        request: MessageGenerate,
        actor: str,
        environment_kind: str = "FIXTURE",
        environment_id: str = "test-env",
    ) -> tuple[ArtifactLineage, ArtifactRevision]:
        """
        Generate message artifact from accepted items or priority reason.
        
        Returns (lineage, revision) tuple.
        Messages start with unconfirmed recipients - require confirmation before send.
        """
        # Validate inputs
        if request.mode == "FOLLOWUP" and not request.accepted_item_refs:
            raise ValueError("FOLLOWUP messages require accepted_item_refs")
        if request.mode == "OUTREACH" and not request.priority_reason_ref:
            raise ValueError("OUTREACH messages require priority_reason_ref")

        # Generate message content (stub - real implementation would use template engine)
        # For now, create a simple message structure
        message = await self._generate_message_content(request, client_id)

        # Create artifact lineage
        artifact_id = uuid4()
        lineage = ArtifactLineage(
            id=artifact_id,
            tenant_id=tenant_id,
            client_id=client_id,
            workflow_id=workflow_id,
            meeting_id=None,  # Messages may not have meeting context
            kind="MESSAGE",
            created_by=actor,
            created_at=datetime.now(UTC),
        )
        self.session.add(lineage)

        # Create first revision
        payload_dict = message.model_dump(mode="json")
        content_hash = self._compute_hash(payload_dict)
        
        revision_id = uuid4()
        revision = ArtifactRevision(
            id=revision_id,
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=artifact_id,
            version=1,
            content_hash=content_hash,
            payload=json.dumps(payload_dict),
            environment_kind=environment_kind,
            environment_id=environment_id,
            created_by=actor,
            created_at=datetime.now(UTC),
        )
        self.session.add(revision)

        # Update lineage to point to current revision
        lineage.current_revision_id = revision_id

        await self.session.commit()
        await self.session.refresh(lineage)
        await self.session.refresh(revision)

        return lineage, revision

    async def _generate_message_content(
        self, request: MessageGenerate, client_id: UUID
    ) -> Message:
        """
        Generate message content from template and basis.
        
        Real implementation would:
        - Load template from config
        - Extract facts from accepted items
        - Apply grounding rules
        - Validate disclosures
        - Return UNCONFIGURED if template/policy missing
        """
        # Stub implementation for testing
        # Real implementation would integrate with template engine and fact extraction
        
        if request.mode == "FOLLOWUP":
            body = "Thank you for our recent meeting. Based on our discussion..."
            subject = "Follow-up from our meeting"
        else:  # OUTREACH
            body = "I wanted to reach out regarding an important matter..."
            subject = "Important update regarding your portfolio"

        # Recipients start unconfirmed - require explicit confirmation
        recipients = [
            MessageRecipient(
                contact_id=f"contact-{client_id}",
                destination="placeholder@example.com",  # Would come from client context
                confirmed=False,
            )
        ]

        # Disclosures must come from approved config
        disclosures = [
            MessageDisclosure(
                ref=request.template_ref,
                text="This communication is for informational purposes only.",
            )
        ]

        # Claims are grounded in evidence
        claims = [
            MessageClaim(
                text="Based on your recent portfolio discussion",
                evidence_refs=[],  # Would reference actual meeting items
                origin=Origin.RECORDED if request.mode == "FOLLOWUP" else Origin.DERIVED,
            )
        ]

        return Message(
            mode=request.mode,
            channel=request.channel,
            template_ref=request.template_ref,
            recipients=recipients,
            subject=subject if request.channel == "EMAIL" else None,
            body=body,
            disclosures=disclosures,
            basis_refs=request.accepted_item_refs,
            priority_reason_ref=request.priority_reason_ref,
            claims=claims,
        )

    async def edit_message(
        self,
        tenant_id: str,
        client_id: UUID,
        artifact_id: UUID,
        recipients: list[MessageRecipient] | None,
        subject: str | None,
        body: str | None,
        actor: str,
        environment_kind: str = "FIXTURE",
        environment_id: str = "test-env",
    ) -> ArtifactRevision:
        """
        Edit message artifact - creates new revision.
        
        Only recipients, subject, and body are editable.
        Template and claims require regeneration.
        """
        # Get current revision
        from sqlalchemy import select
        
        stmt = select(ArtifactRevision).join(
            ArtifactLineage,
            ArtifactRevision.artifact_id == ArtifactLineage.id
        ).where(
            ArtifactLineage.tenant_id == tenant_id,
            ArtifactLineage.client_id == client_id,
            ArtifactLineage.id == artifact_id,
            ArtifactRevision.id == ArtifactLineage.current_revision_id,
        )
        result = await self.session.execute(stmt)
        current_revision = result.scalar_one_or_none()
        
        if not current_revision:
            raise ValueError("Message artifact not found")

        # Parse current message
        current_message = Message.model_validate_json(current_revision.payload)

        # Apply edits
        if recipients is not None:
            current_message.recipients = recipients
        if subject is not None:
            current_message.subject = subject
        if body is not None:
            current_message.body = body

        # Create new revision
        payload_dict = current_message.model_dump(mode="json")
        content_hash = self._compute_hash(payload_dict)
        
        revision_id = uuid4()
        new_revision = ArtifactRevision(
            id=revision_id,
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=artifact_id,
            version=current_revision.version + 1,
            content_hash=content_hash,
            payload=json.dumps(payload_dict),
            environment_kind=environment_kind,
            environment_id=environment_id,
            created_by=actor,
            created_at=datetime.now(UTC),
        )
        self.session.add(new_revision)

        # Update lineage
        stmt = select(ArtifactLineage).where(
            ArtifactLineage.tenant_id == tenant_id,
            ArtifactLineage.client_id == client_id,
            ArtifactLineage.id == artifact_id,
        )
        result = await self.session.execute(stmt)
        lineage = result.scalar_one()
        lineage.current_revision_id = revision_id

        await self.session.commit()
        await self.session.refresh(new_revision)

        return new_revision
