"""Brief generation service using frozen workflow context per U-006.

Generates canonical five-section briefs with truthful source states and provenance.
Never fabricates portfolio/interaction data; uses frozen workflow context.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ArtifactItem, ArtifactLineage, ArtifactRevision
from app.models.models import Brief as BriefModel
from app.models.workflow import Workflow
from app.repositories.artifacts import ArtifactRepository, RevisionRepository
from app.schemas.brief import (
    AgendaItem,
    Brief,
    BriefClaim,
    BriefSection,
    BriefSections,
)
from app.schemas.common import (
    Availability,
    CapabilityState,
    Completeness,
    Environment,
    EnvironmentKind,
    EvidenceRef,
    Origin,
    ReviewState,
    Source,
)

logger = logging.getLogger(__name__)


class BriefGenerator:
    """Generates briefs from frozen workflow context with truthful source states."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.artifact_repo = ArtifactRepository(session)
        self.revision_repo = RevisionRepository(session)

    async def generate_brief(
        self,
        tenant_id: str,
        client_id: UUID,
        workflow_id: UUID,
        meeting_id: UUID | None,
        section_keys: list[str],
        actor: str,
        previous_artifact_id: UUID | None = None,
    ) -> Brief:
        """Generate brief with five sections from workflow context.
        
        Uses frozen context from U-006 workflow orchestrator. Never fabricates
        portfolio/interaction data - truthfully represents UNAVAILABLE when sources absent.
        """
        # Fetch workflow to get context_revision
        workflow = await self.session.get(Workflow, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Environment for fixtures (production would use INSTITUTION_TEST/PRODUCTION)
        environment = Environment(kind=EnvironmentKind.FIXTURE, id="test-env-001")

        # Generate all five sections with truthful states
        sections_dict = {}
        for key in ["portfolio_overview", "material_changes", "recent_interactions", "market_news", "proposed_agenda"]:
            sections_dict[key] = await self._generate_section(
                key, tenant_id, client_id, workflow, environment
            )

        sections = BriefSections(**sections_dict)

        # Create artifact lineage if new, or reuse existing for regeneration
        if previous_artifact_id:
            lineage = await self.artifact_repo.get(tenant_id, client_id, previous_artifact_id)
            if not lineage:
                raise ValueError(f"Previous artifact {previous_artifact_id} not found")
            next_version = await self._get_next_version(tenant_id, previous_artifact_id)
        else:
            lineage = await self.artifact_repo.create_lineage(
                tenant_id=tenant_id,
                client_id=client_id,
                workflow_id=workflow_id,
                meeting_id=meeting_id,
                kind="BRIEF",
                created_by=actor,
            )
            next_version = 1

        # Compute content hash for entire brief sections
        content_hash = self._compute_sections_hash(sections)

        # Create immutable revision with BRIEF pointer payload
        revision = await self.revision_repo.create_revision(
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=lineage.id,
            version=next_version,
            content_hash=content_hash,
            payload=json.dumps({"brief_id": str(lineage.id)}),
            environment_kind=environment.kind.value,
            environment_id=environment.id,
            created_by=actor,
        )

        # Create artifact items for each section
        await self._create_section_items(tenant_id, client_id, revision.id, sections)

        # Update lineage current pointer
        lineage.current_revision_id = revision.id
        await self.session.flush()

        # Store in legacy briefs table with canonical sections JSON
        await self._persist_legacy_brief(
            lineage.id, client_id, workflow_id, meeting_id, next_version,
            tenant_id, revision.id, sections, actor
        )

        await self.session.commit()

        # Build response
        brief = Brief(
            brief_id=lineage.id,
            artifact_ref={
                "artifact_id": lineage.id,
                "revision_id": revision.id,
                "version": next_version,
                "hash": content_hash,
            },
            workflow_id=workflow_id,
            meeting_id=meeting_id,
            client_id=client_id,
            generated_at=revision.created_at,
            generated_by=actor,
            review_state=ReviewState.UNREVIEWED,
            version=next_version,
            environment=environment,
            source_cutoff=datetime.now(timezone.utc),
            sections=sections,
            blockers=[],
        )

        return brief

    async def _generate_section(
        self, key: str, tenant_id: str, client_id: UUID, workflow: Workflow, environment: Environment
    ) -> BriefSection:
        """Generate single section with truthful source states.
        
        Real implementation would call U-006 context services to fetch
        portfolio/calendar/interactions. Here we demonstrate contract structure.
        """
        # Placeholder: Real implementation uses frozen context from U-006
        # For now, return UNAVAILABLE state to be truthful
        source = Source(
            id=uuid4(),
            environment=environment,
            availability=Availability.UNAVAILABLE,
            origin=Origin.RECORDED,
            live_response=False,
            limitation_codes=["PROVIDER_UNCONFIGURED"],
        )

        section_hash = self._compute_item_hash({"key": key, "narrative": None, "claims": [], "agenda": []})

        return BriefSection(
            key=key,
            item_hash=section_hash,
            narrative=None,
            claims=[],
            agenda=[],
            availability=Availability.UNAVAILABLE,
            completeness=Completeness.EMPTY,
            capability_state=CapabilityState.UNCONFIGURED,
            review_state=ReviewState.UNREVIEWED,
            sources=[source],
            limitations=["Context provider not configured - demonstrating contract structure"],
        )

    async def _create_section_items(
        self, tenant_id: str, client_id: UUID, revision_id: UUID, sections: BriefSections
    ) -> None:
        """Create artifact_items for each section."""
        for key in ["portfolio_overview", "material_changes", "recent_interactions", "market_news", "proposed_agenda"]:
            section = getattr(sections, key)
            item = ArtifactItem(
                tenant_id=tenant_id,
                client_id=client_id,
                revision_id=revision_id,
                item_key=key,
                item_hash=section.item_hash,
                status="UNREVIEWED",
            )
            self.session.add(item)

    async def _persist_legacy_brief(
        self,
        brief_id: UUID,
        client_id: UUID,
        workflow_id: UUID,
        meeting_id: UUID | None,
        version: int,
        tenant_id: str,
        revision_id: UUID,
        sections: BriefSections,
        actor: str,
    ) -> None:
        """Persist to legacy briefs table with canonical sections JSON."""
        sections_json = {
            "portfolio_overview": self._section_to_dict(sections.portfolio_overview),
            "material_changes": self._section_to_dict(sections.material_changes),
            "recent_interactions": self._section_to_dict(sections.recent_interactions),
            "market_news": self._section_to_dict(sections.market_news),
            "proposed_agenda": self._section_to_dict(sections.proposed_agenda),
        }

        brief_model = BriefModel(
            id=brief_id,
            client_id=client_id,
            version=str(version),
            sections=sections_json,
            generated_at=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            meeting_id=meeting_id,
            artifact_id=brief_id,
            artifact_revision_id=revision_id,
            revision_no=version,
        )
        self.session.add(brief_model)

    def _section_to_dict(self, section: BriefSection) -> dict[str, Any]:
        """Convert section to dict for JSON storage."""
        return {
            "key": section.key.value,
            "item_hash": section.item_hash,
            "narrative": section.narrative,
            "claims": [
                {
                    "id": c.id,
                    "text": c.text,
                    "origin": c.origin.value,
                    "evidence_refs": [{"source_id": str(e.source_id), "source_version": e.source_version} for e in c.evidence_refs],
                    "confidence": float(c.confidence) if c.confidence else None,
                }
                for c in section.claims
            ],
            "agenda": [
                {
                    "id": a.id,
                    "text": a.text,
                    "origin": a.origin.value,
                    "evidence_refs": [{"source_id": str(e.source_id), "source_version": e.source_version} for e in a.evidence_refs],
                }
                for a in section.agenda
            ],
            "availability": section.availability.value,
            "completeness": section.completeness.value,
            "capability_state": section.capability_state.value,
            "review_state": section.review_state.value,
            "sources": [self._source_to_dict(s) for s in section.sources],
            "limitations": section.limitations,
        }

    def _source_to_dict(self, source: Source) -> dict[str, Any]:
        """Convert source to dict for JSON storage."""
        return {
            "id": str(source.id),
            "environment": {"kind": source.environment.kind.value, "id": source.environment.id},
            "availability": source.availability.value,
            "origin": source.origin.value,
            "system_key": source.system_key,
            "record_id": source.record_id,
            "record_version": source.record_version,
            "as_of": source.as_of.isoformat() if source.as_of else None,
            "retrieved_at": source.retrieved_at.isoformat() if source.retrieved_at else None,
            "authoritative_owner": source.authoritative_owner,
            "live_response": source.live_response,
            "adapter_receipt_id": source.adapter_receipt_id,
            "confidence": float(source.confidence) if source.confidence else None,
            "limitation_codes": source.limitation_codes,
        }

    def _compute_sections_hash(self, sections: BriefSections) -> str:
        """Compute SHA-256 hash of canonical sections JSON."""
        canonical = {
            "portfolio_overview": self._section_canonical(sections.portfolio_overview),
            "material_changes": self._section_canonical(sections.material_changes),
            "recent_interactions": self._section_canonical(sections.recent_interactions),
            "market_news": self._section_canonical(sections.market_news),
            "proposed_agenda": self._section_canonical(sections.proposed_agenda),
        }
        json_bytes = json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(json_bytes).hexdigest()

    def _section_canonical(self, section: BriefSection) -> dict[str, Any]:
        """Convert section to canonical form for hashing."""
        return {
            "key": section.key.value,
            "narrative": section.narrative,
            "claims": [{"id": c.id, "text": c.text, "origin": c.origin.value} for c in section.claims],
            "agenda": [{"id": a.id, "text": a.text, "origin": a.origin.value} for a in section.agenda],
        }

    def _compute_item_hash(self, item_data: dict[str, Any]) -> str:
        """Compute SHA-256 hash of item canonical JSON."""
        json_bytes = json.dumps(item_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(json_bytes).hexdigest()

    async def _get_next_version(self, tenant_id: str, artifact_id: UUID) -> int:
        """Get next version number for artifact."""
        current = await self.revision_repo.get_current_revision(tenant_id, None, artifact_id)
        return (current.version + 1) if current else 1
