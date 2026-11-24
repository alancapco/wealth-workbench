"""Brief generation service using frozen workflow context per U-006.

Generates canonical five-section briefs with truthful source states and provenance.
Sections are assembled from recorded client, holdings, interaction and meeting
rows plus market provider data; absent providers degrade with explicit states.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.artifact import ArtifactItem, ArtifactLineage, ArtifactRevision
from app.models.models import Brief as BriefModel, Client, Holding, Interaction
from app.models.workflow import Meeting, Workflow
from app.repositories.artifacts import ArtifactRepository, RevisionRepository
from app.schemas.brief import AgendaItem, Brief, BriefClaim, BriefSection, BriefSections
from app.schemas.common import (
    ArtifactRef,
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
from app.services.market.market_service import market_data_service

logger = logging.getLogger(__name__)

SECTION_KEYS = (
    "portfolio_overview",
    "material_changes",
    "recent_interactions",
    "market_news",
    "proposed_agenda",
)
MATERIAL_MOVE_THRESHOLD = 2.0


def canonical_hash(data: dict) -> str:
    """SHA-256 of canonical JSON, matching MessageService._compute_hash."""
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


class BriefArtifactRef(ArtifactRef):
    """ArtifactRef that also supports dict-style access used by existing brief callers."""

    def __getitem__(self, key: str):
        return getattr(self, key)


class BriefGenerator:
    """Generates briefs from recorded workflow context with truthful source states."""

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
        """Generate a five-section brief with a real artifact lineage and revision."""
        workflow = await self.session.get(Workflow, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        environment = Environment(kind=EnvironmentKind.FIXTURE, id="test-env-001")
        context = await self._collect_context(tenant_id, client_id, workflow)

        sections_dict = {}
        for key in SECTION_KEYS:
            sections_dict[key] = self._generate_section(key, context, environment, sections_dict)
        sections = BriefSections(**sections_dict)
        sections_json = self._sections_to_dict(sections)
        content_hash = canonical_hash(sections_json)

        if previous_artifact_id:
            lineage = await self.artifact_repo.get_by_id(tenant_id, client_id, previous_artifact_id)
            if not lineage:
                raise ValueError(f"Previous artifact {previous_artifact_id} not found")
            next_version = await self._get_next_version(tenant_id, client_id, lineage.id)
        else:
            lineage = ArtifactLineage(
                id=uuid4(),
                tenant_id=tenant_id,
                client_id=client_id,
                workflow_id=workflow_id,
                meeting_id=meeting_id,
                kind="BRIEF",
                created_by=actor,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(lineage)
            await self.session.flush()
            next_version = 1

        revision = ArtifactRevision(
            id=uuid4(),
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=lineage.id,
            version=next_version,
            content_hash=content_hash,
            payload=json.dumps({"brief_id": str(lineage.id), "sections": sections_json}),
            environment_kind=environment.kind.value,
            environment_id=environment.id,
            created_by=actor,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(revision)
        await self.session.flush()

        await self._create_section_items(tenant_id, client_id, revision.id, sections)
        lineage.current_revision_id = revision.id
        await self.session.flush()

        await self._persist_legacy_brief(
            lineage.id, client_id, workflow_id, meeting_id, next_version,
            tenant_id, revision.id, sections_json, content_hash, actor
        )

        await self.session.commit()

        return Brief(
            brief_id=lineage.id,
            artifact_ref=BriefArtifactRef(
                artifact_id=lineage.id,
                revision_id=revision.id,
                version=next_version,
                hash=content_hash,
            ),
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

    async def _collect_context(
        self, tenant_id: str, client_id: UUID, workflow: Workflow
    ) -> dict[str, Any]:
        client = await self.session.get(Client, client_id)
        holdings = list((await self.session.execute(
            select(Holding).where(Holding.client_id == client_id)
        )).scalars().all())
        interactions = list((await self.session.execute(
            select(Interaction)
            .where(Interaction.client_id == client_id)
            .order_by(Interaction.interaction_date.desc())
            .limit(5)
        )).scalars().all())
        meetings = list((await self.session.execute(
            select(Meeting)
            .where(Meeting.tenant_id == tenant_id, Meeting.client_id == client_id)
            .order_by(Meeting.starts_at.desc())
            .limit(5)
        )).scalars().all())
        movements, news, news_source = await self._collect_market(holdings)
        quote_configured = bool((settings.ALPHAVANTAGE_API_KEY or "").strip())
        news_configured = market_data_service.news_configured

        return {
            "client": client,
            "holdings": holdings,
            "interactions": interactions,
            "meetings": meetings,
            "workflow": workflow,
            "movements": movements,
            "news": news,
            "news_source": news_source,
            "quote_configured": quote_configured,
            "news_configured": news_configured,
        }

    async def _collect_market(
        self, holdings: list[Holding]
    ) -> tuple[list[dict], list[dict], str]:
        symbols = [h.symbol for h in holdings if h.symbol]
        quote_configured = bool((settings.ALPHAVANTAGE_API_KEY or "").strip())

        quotes = []
        if symbols and quote_configured:
            try:
                quotes = await market_data_service.get_real_time_quote(symbols)
            except Exception as e:
                logger.warning("Quote provider unavailable: %s", e)
        by_symbol = {q.get("symbol"): q for q in quotes if isinstance(q, dict)}

        movements = []
        for holding in holdings:
            quote = by_symbol.get(holding.symbol)
            if not quote or quote.get("change_percent") is None:
                continue
            pct = float(quote["change_percent"])
            movements.append({
                "symbol": holding.symbol,
                "change_percent": pct,
                "price": float(quote.get("price") or 0),
                "impact": (holding.current_value or 0) * abs(pct) / 100,
                "material": abs(pct) >= MATERIAL_MOVE_THRESHOLD,
                "quoted_symbol": quote.get("quoted_symbol"),
                "source_id": quote.get("source_id"),
                "feed_timestamp": quote.get("feed_timestamp"),
            })

        news: list[dict] = []
        news_source = "none"
        news_configured = market_data_service.news_configured
        if news_configured:
            try:
                news, news_source, _ = await market_data_service.get_market_news(
                    symbols=symbols or None, limit=4
                )
                if not news:
                    news, news_source, _ = await market_data_service.get_market_news(limit=4)
            except Exception as e:
                logger.warning("News provider unavailable: %s", e)

        return movements, news or [], news_source

    def _generate_section(
        self, key: str, context: dict, environment: Environment, built: dict[str, BriefSection]
    ) -> BriefSection:
        if key == "portfolio_overview":
            return self._portfolio_section(context, environment)
        if key == "material_changes":
            return self._material_changes_section(context, environment)
        if key == "recent_interactions":
            return self._interactions_section(context, environment)
        if key == "market_news":
            return self._market_news_section(context, environment)
        return self._agenda_section(context, environment, built)

    @staticmethod
    def _make_source(
        environment: Environment,
        system_key: str,
        record_id: str,
        *,
        availability: Availability = Availability.AVAILABLE,
        origin: Origin = Origin.RECORDED,
        as_of: datetime | None = None,
        record_version: str | None = None,
        authoritative_owner: str | None = None,
        limitation_codes: list[str] | None = None,
    ) -> Source:
        # Source ids are derived from the underlying record, never random placeholders.
        return Source(
            id=uuid5(NAMESPACE_URL, f"{system_key}:{record_id}:{record_version or ''}"),
            environment=environment,
            availability=availability,
            origin=origin,
            system_key=system_key,
            record_id=record_id,
            record_version=record_version,
            as_of=as_of,
            retrieved_at=None,
            authoritative_owner=authoritative_owner,
            live_response=False,
            limitation_codes=limitation_codes or [],
        )

    @staticmethod
    def _refs(sources: list[Source]) -> list[EvidenceRef]:
        return [EvidenceRef(source_id=s.id, source_version=s.record_version) for s in sources]

    def _make_section(
        self,
        key: str,
        *,
        narrative: str | None,
        claims: list[BriefClaim],
        agenda: list[AgendaItem],
        sources: list[Source],
        availability: Availability,
        completeness: Completeness,
        capability_state: CapabilityState,
        limitations: list[str],
    ) -> BriefSection:
        canonical = {
            "key": key,
            "narrative": narrative,
            "claims": [{"id": c.id, "text": c.text, "origin": c.origin.value} for c in claims],
            "agenda": [{"id": a.id, "text": a.text, "origin": a.origin.value} for a in agenda],
        }
        return BriefSection(
            key=key,
            item_hash=canonical_hash(canonical),
            narrative=narrative,
            claims=claims,
            agenda=agenda,
            availability=availability,
            completeness=completeness,
            capability_state=capability_state,
            review_state=ReviewState.UNREVIEWED,
            sources=sources,
            limitations=limitations,
        )

    def _unavailable_section(
        self,
        key: str,
        environment: Environment,
        code: str,
        message: str,
        capability_state: CapabilityState = CapabilityState.UNAVAILABLE,
    ) -> BriefSection:
        source = self._make_source(
            environment, "unavailable", f"{key}:{code}",
            availability=Availability.UNAVAILABLE,
            limitation_codes=[code],
        )
        return self._make_section(
            key, narrative=None, claims=[], agenda=[], sources=[source],
            availability=Availability.UNAVAILABLE,
            completeness=Completeness.EMPTY,
            capability_state=capability_state,
            limitations=[message],
        )

    def _portfolio_section(self, context: dict, environment: Environment) -> BriefSection:
        client: Client | None = context["client"]
        holdings: list[Holding] = context["holdings"]
        if client is None:
            return self._unavailable_section(
                "portfolio_overview", environment, "CLIENT_RECORD_MISSING",
                "Client record not found; portfolio context is unavailable."
            )

        currency = client.currency or "USD"
        client_source = self._make_source(environment, "clients", str(client.id))
        sources = [client_source]
        claims = [BriefClaim(
            id=f"portfolio_overview:client:{client.id}",
            text=(f"{client.name} | AUM {currency} {client.aum or 0:,.0f} | "
                  f"risk profile {client.risk_profile or 'not recorded'}"),
            origin=Origin.RECORDED,
            evidence_refs=self._refs([client_source]),
            confidence=1.0,
        )]

        total = 0.0
        for holding in holdings:
            value = holding.current_value or 0
            total += value
            source = self._make_source(
                environment, "holdings", str(holding.id),
                as_of=holding.as_of,
                record_version=holding.as_of.isoformat() if holding.as_of else None,
                authoritative_owner=holding.source_kind,
            )
            sources.append(source)
            claims.append(BriefClaim(
                id=f"portfolio_overview:holding:{holding.id}",
                text=(f"{holding.symbol}: {holding.quantity or 0:g} units, "
                      f"{holding.asset_class or 'unclassified'}, "
                      f"recorded value {currency} {value:,.0f}"),
                origin=Origin.RECORDED,
                evidence_refs=self._refs([source]),
                confidence=1.0,
            ))

        narrative = (f"{client.name}: {len(holdings)} recorded holdings, "
                     f"total recorded value {currency} {total:,.0f}.")
        limitations = [] if holdings else ["No holdings recorded; totals reflect the client record only."]
        return self._make_section(
            "portfolio_overview", narrative=narrative, claims=claims, agenda=[],
            sources=sources, availability=Availability.AVAILABLE,
            completeness=Completeness.COMPLETE if holdings else Completeness.PARTIAL,
            capability_state=CapabilityState.READY, limitations=limitations,
        )

    def _material_changes_section(self, context: dict, environment: Environment) -> BriefSection:
        movements = context["movements"]
        if not movements:
            configured = context["quote_configured"]
            return self._unavailable_section(
                "material_changes", environment,
                "MARKET_QUOTES_UNAVAILABLE" if configured else "MARKET_QUOTES_UNCONFIGURED",
                "No live quote data available; price moves are not shown.",
                CapabilityState.UNAVAILABLE if configured else CapabilityState.UNCONFIGURED,
            )

        client: Client | None = context["client"]
        currency = (client.currency if client else None) or "USD"
        sources, claims, material_symbols = [], [], []
        for move in movements:
            version = str(move["feed_timestamp"] or "")
            source = self._make_source(
                environment, "market_quotes", move["symbol"],
                record_version=version or None,
                authoritative_owner=move["source_id"],
            )
            sources.append(source)
            claims.append(BriefClaim(
                id=f"material_changes:quote:{move['symbol']}",
                text=(f"{move['symbol']} moved {move['change_percent']:+.2f}% to "
                      f"{move['price']:.2f}; position impact {currency} {move['impact']:,.0f}."
                      + (" Material move." if move["material"] else " Within the 2% material threshold.")),
                origin=Origin.DERIVED,
                evidence_refs=self._refs([source]),
                confidence=1.0,
            ))
            if move["material"]:
                material_symbols.append(f"{move['symbol']} {move['change_percent']:+.2f}%")

        narrative = ("Material moves: " + ", ".join(material_symbols)) if material_symbols else \
            "No holding exceeded the 2% material-move threshold."
        return self._make_section(
            "material_changes", narrative=narrative, claims=claims, agenda=[],
            sources=sources, availability=Availability.AVAILABLE,
            completeness=Completeness.COMPLETE, capability_state=CapabilityState.READY,
            limitations=[],
        )

    def _interactions_section(self, context: dict, environment: Environment) -> BriefSection:
        interactions: list[Interaction] = context["interactions"]
        if not interactions:
            return self._unavailable_section(
                "recent_interactions", environment, "NO_INTERACTIONS_RECORDED",
                "No interactions recorded for this client."
            )

        sources, claims = [], []
        for interaction in interactions:
            when = interaction.interaction_date
            source = self._make_source(
                environment, "interactions", str(interaction.id),
                as_of=when, record_version=str(interaction.id),
            )
            sources.append(source)
            kind = (interaction.interaction_type or "interaction").replace("_", " ").title()
            claims.append(BriefClaim(
                id=f"recent_interactions:{interaction.id}",
                text=(f"{kind} on {when.date().isoformat() if when else 'undated'}: "
                      f"{interaction.summary or 'No summary recorded.'}"),
                origin=Origin.RECORDED,
                evidence_refs=self._refs([source]),
                confidence=float(interaction.confidence) if interaction.confidence is not None else 1.0,
            ))

        return self._make_section(
            "recent_interactions",
            narrative=f"{len(interactions)} most recent recorded interactions.",
            claims=claims, agenda=[], sources=sources,
            availability=Availability.AVAILABLE, completeness=Completeness.PARTIAL,
            capability_state=CapabilityState.READY, limitations=[],
        )

    def _market_news_section(self, context: dict, environment: Environment) -> BriefSection:
        news: list[dict] = context["news"]
        if not news:
            configured = context["news_configured"]
            return self._unavailable_section(
                "market_news", environment, "MARKET_NEWS_UNAVAILABLE",
                "Market news provider returned no items.",
                CapabilityState.UNAVAILABLE if configured else CapabilityState.UNCONFIGURED,
            )

        sources, claims = [], []
        for item in news:
            record_id = str(item.get("url") or item.get("id") or item.get("title") or "")
            source = self._make_source(
                environment, "market_news", record_id,
                record_version=str(item.get("timestamp") or "") or None,
                authoritative_owner=item.get("source") or context["news_source"],
            )
            sources.append(source)
            summary = (item.get("content") or "").strip()
            text = f"{item.get('title') or 'Untitled'}"
            if summary:
                text += f": {summary[:240]}"
            claims.append(BriefClaim(
                id=f"market_news:{record_id}",
                text=text,
                origin=Origin.RECORDED,
                evidence_refs=self._refs([source]),
                confidence=1.0,
            ))

        return self._make_section(
            "market_news", narrative=f"{len(news)} market news items from the configured provider.",
            claims=claims, agenda=[], sources=sources,
            availability=Availability.AVAILABLE, completeness=Completeness.PARTIAL,
            capability_state=CapabilityState.READY, limitations=[],
        )

    def _agenda_section(
        self, context: dict, environment: Environment, built: dict[str, BriefSection]
    ) -> BriefSection:
        agenda: list[AgendaItem] = []
        material = [m for m in context["movements"] if m["material"]]
        if material:
            symbols = ", ".join(dict.fromkeys(m["symbol"] for m in material))
            largest = max(material, key=lambda m: abs(m["change_percent"]))
            agenda.append(AgendaItem(
                id="proposed_agenda:material_moves",
                text=(f"Review material price moves in {symbols} "
                      f"(largest: {largest['symbol']} {largest['change_percent']:+.2f}%) "
                      "and their position impact."),
                origin=Origin.DERIVED,
                evidence_refs=self._refs(built["material_changes"].sources),
            ))

        meeting_sources = []
        for meeting in context["meetings"][:2]:
            source = self._make_source(
                environment, "meetings", str(meeting.id),
                as_of=meeting.starts_at, record_version=str(meeting.row_version),
            )
            meeting_sources.append(source)
            date_label = meeting.starts_at.date().isoformat() if meeting.starts_at else "date not set"
            agenda.append(AgendaItem(
                id=f"proposed_agenda:meeting:{meeting.id}",
                text=f"Prepare for {meeting.title or 'recorded meeting'} on {date_label}.",
                origin=Origin.DERIVED,
                evidence_refs=self._refs([source]),
            ))

        interactions: list[Interaction] = context["interactions"]
        if interactions:
            latest = interactions[0]
            when = latest.interaction_date
            agenda.append(AgendaItem(
                id="proposed_agenda:latest_interaction",
                text=(f"Follow up on the {(latest.interaction_type or 'interaction').replace('_', ' ')} "
                      f"from {when.date().isoformat() if when else 'undated'}."),
                origin=Origin.DERIVED,
                evidence_refs=self._refs(built["recent_interactions"].sources),
            ))

        if not agenda:
            return self._unavailable_section(
                "proposed_agenda", environment, "NO_AGENDA_INPUTS",
                "No recorded context available to propose an agenda."
            )

        sources: list[Source] = []
        seen = set()
        for section in built.values():
            for source in section.sources:
                if source.id not in seen:
                    seen.add(source.id)
                    sources.append(source)
        for source in meeting_sources:
            if source.id not in seen:
                seen.add(source.id)
                sources.append(source)

        return self._make_section(
            "proposed_agenda",
            narrative=f"{len(agenda)} agenda items derived from recorded holdings, meetings and interactions.",
            claims=[], agenda=agenda, sources=sources,
            availability=Availability.AVAILABLE, completeness=Completeness.PARTIAL,
            capability_state=CapabilityState.READY, limitations=[],
        )

    async def _create_section_items(
        self, tenant_id: str, client_id: UUID, revision_id: UUID, sections: BriefSections
    ) -> None:
        """Create artifact_items for each section."""
        for key in SECTION_KEYS:
            section = getattr(sections, key)
            self.session.add(ArtifactItem(
                tenant_id=tenant_id,
                client_id=client_id,
                revision_id=revision_id,
                item_key=key,
                item_hash=section.item_hash,
                status="UNREVIEWED",
            ))

    async def _persist_legacy_brief(
        self,
        brief_id: UUID,
        client_id: UUID,
        workflow_id: UUID,
        meeting_id: UUID | None,
        version: int,
        tenant_id: str,
        revision_id: UUID,
        sections_json: dict[str, Any],
        content_hash: str,
        actor: str,
    ) -> None:
        """Persist canonical sections JSON; regeneration updates the existing row."""
        fields = {
            "client_id": client_id,
            "version": str(version),
            "sections": sections_json,
            # briefs.generated_at is TIMESTAMP WITHOUT TIME ZONE; keep it naive UTC.
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None),
            "tenant_id": tenant_id,
            "workflow_id": workflow_id,
            "meeting_id": meeting_id,
            "artifact_id": brief_id,
            "artifact_revision_id": revision_id,
            "revision_no": version,
            "content_hash": content_hash,
            "generated_by": actor,
        }
        existing = await self.session.get(BriefModel, brief_id)
        if existing:
            for field, value in fields.items():
                setattr(existing, field, value)
        else:
            self.session.add(BriefModel(id=brief_id, **fields))

    def _sections_to_dict(self, sections: BriefSections) -> dict[str, Any]:
        return {key: self._section_to_dict(getattr(sections, key)) for key in SECTION_KEYS}

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

    async def _get_next_version(self, tenant_id: str, client_id: UUID, artifact_id: UUID) -> int:
        """Get next version number for artifact."""
        current = await self.revision_repo.get_current_revision(tenant_id, client_id, artifact_id)
        return (current.version + 1) if current else 1
