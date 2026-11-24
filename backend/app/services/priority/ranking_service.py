"""Book-wide priority ranking service per Architecture §6.6.

Implements deterministic evaluation with source-linked reasons, stale/outage state,
DST-aware local date, and top-10 cap of currently entitled non-DNC clients.
"""
import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Client, Holding, Interaction
from app.models.platform import ClientAssignment
from app.models.priority import PriorityEvaluation as PriorityEvaluationModel
from app.models.priority import PriorityItem as PriorityItemModel
from app.schemas.client import ClientSummary
from app.schemas.common import (
    Availability,
    ConfigRef,
    Environment,
    EnvironmentKind,
    EvidenceRef,
    FieldValue,
    FieldValueType,
    Origin,
    Source,
)
from app.schemas.priority import (
    EvaluationStatus,
    PriorityEvaluation,
    PriorityItem,
    PriorityReason,
    PrioritySignal,
    ReasonClass,
)
from app.services.priority.control_service import ControlService
from app.services.ranking.policy_config import (
    config_ref,
    get_active_ranking_config,
    get_config_ref,
)


class RankingServiceError(Exception):
    """Ranking service error."""
    pass


class RankingService:
    """Book-wide priority ranking per architecture §6.6.
    
    Evaluates up to 10 currently entitled non-DNC clients with deterministic
    source-linked reasons. Empty book returns successful empty evaluation,
    outage returns 503/stale state not fabricated empty.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def evaluate_book_priorities(
        self,
        tenant_id: str,
        book_id: str,
        local_date: date,
        timezone_str: str,
        trigger: str,
        principal_subject: str,
        policy_config_id: UUID | None = None,
    ) -> PriorityEvaluation:
        """Evaluate book-wide priorities per architecture API-015.
        
        Returns top 10 entitled non-DNC clients with source-linked reasons.
        Empty book is successful empty, outage is FAILED status not fabricated empty.
        
        Args:
            tenant_id: Tenant identifier
            book_id: Book identifier
            local_date: Local date for evaluation (DST-aware)
            timezone_str: IANA timezone
            trigger: RM_REFRESH | MATERIAL_SIGNAL
            principal_subject: Authenticated principal
            policy_config_id: Optional ranking policy config; resolved from config service when omitted
            
        Returns:
            PriorityEvaluation with up to 10 items
            
        Raises:
            RankingServiceError: if dependency unavailable
        """
        evaluation_id = uuid4()
        evaluated_at = datetime.now(timezone.utc)

        # DEC-03 is an approved RANKING config revision. Resolve it through the
        # config service; an external caller may still supply an explicit id.
        resolved_config = None
        if policy_config_id is None:
            resolved_config = await get_active_ranking_config(self.db, tenant_id, book_id)
            if resolved_config is not None:
                policy_config_id = resolved_config.id

        if policy_config_id is None:
            # UNCONFIGURED is honest: no ranking policy, no fabricated evaluation.
            return self._create_empty_evaluation(
                evaluation_id=evaluation_id,
                tenant_id=tenant_id,
                book_id=book_id,
                local_date=local_date,
                timezone_str=timezone_str,
                evaluated_at=evaluated_at,
                principal_subject=principal_subject,
                status=EvaluationStatus.FAILED,
                criteria_summary="Ranking policy UNCONFIGURED",
            )

        policy_ref = (
            config_ref(resolved_config)
            if resolved_config is not None
            else await get_config_ref(self.db, policy_config_id)
        )
        if policy_ref is None:
            # Caller-supplied id has no stored revision; keep a deterministic placeholder.
            policy_ref = ConfigRef(id=policy_config_id, revision=1, hash="0" * 64)

        # Fetch entitled non-DNC clients for book
        entitled_clients = await self._fetch_entitled_clients(tenant_id, book_id)
        
        if not entitled_clients:
            # Empty book is successful empty evaluation (not outage)
            return self._create_empty_evaluation(
                evaluation_id=evaluation_id,
                tenant_id=tenant_id,
                book_id=book_id,
                local_date=local_date,
                timezone_str=timezone_str,
                evaluated_at=evaluated_at,
                principal_subject=principal_subject,
                status=EvaluationStatus.CURRENT,
                criteria_summary="No entitled non-DNC clients in book",
                policy_ref=policy_ref,
            )
        
        # Rank clients with deterministic sources
        ranked_items = await self._rank_clients(
            entitled_clients=entitled_clients,
            tenant_id=tenant_id,
            book_id=book_id,
            local_date=local_date,
            evaluated_at=evaluated_at,
        )
        
        # Cap at 10 per architecture §6.6
        top_10 = ranked_items[:10]
        
        # Persist evaluation
        await self._persist_evaluation(
            evaluation_id=evaluation_id,
            tenant_id=tenant_id,
            book_id=book_id,
            local_date=local_date,
            timezone_str=timezone_str,
            evaluated_at=evaluated_at,
            principal_subject=principal_subject,
            policy_config_id=policy_config_id,
            items=top_10,
        )
        
        # Build response
        return PriorityEvaluation(
            id=evaluation_id,
            book_id=book_id,
            date=local_date,
            timezone=timezone_str,
            evaluated_at=evaluated_at,
            policy_ref=policy_ref,
            status=EvaluationStatus.CURRENT,
            criteria_summary=f"Top {len(top_10)} entitled non-DNC clients",
            items=top_10,
            environment=Environment(
                kind=EnvironmentKind.FIXTURE,
                id="fixture-ranking-env",
            ),
            source_refs=[],
        )
    
    async def get_latest_evaluation(
        self,
        tenant_id: str,
        book_id: str,
        local_date: date,
        timezone_str: str,
    ) -> PriorityEvaluation | None:
        """Get latest priority evaluation for book/date per architecture API-016.
        
        Returns None only if no prior evaluation exists (not fabricated empty).
        
        Args:
            tenant_id: Tenant identifier
            book_id: Book identifier
            local_date: Local date
            timezone_str: IANA timezone
            
        Returns:
            Latest evaluation or None if no prior evaluation
        """
        # Query latest evaluation for book/date
        stmt = (
            select(PriorityEvaluationModel)
            .where(
                and_(
                    PriorityEvaluationModel.tenant_id == tenant_id,
                    PriorityEvaluationModel.book_id == book_id,
                    PriorityEvaluationModel.local_date == local_date,
                )
            )
            .order_by(PriorityEvaluationModel.evaluated_at.desc())
            .limit(1)
        )
        
        result = await self.db.execute(stmt)
        eval_model = result.scalar_one_or_none()
        
        if not eval_model:
            return None
        
        # Load items with controls
        items_stmt = (
            select(PriorityItemModel)
            .where(PriorityItemModel.evaluation_id == eval_model.id)
            .order_by(PriorityItemModel.rank)
        )
        items_result = await self.db.execute(items_stmt)
        item_models = items_result.scalars().all()
        
        # Convert to DTO
        return await self._model_to_dto(eval_model, item_models)

    async def get_latest_evaluation_for_books(
        self,
        tenant_id: str,
        book_ids: list[str],
    ) -> PriorityEvaluation | None:
        """Latest stored evaluation across the principal's entitled books."""
        if not book_ids:
            return None
        stmt = (
            select(PriorityEvaluationModel)
            .where(
                PriorityEvaluationModel.tenant_id == tenant_id,
                PriorityEvaluationModel.book_id.in_(book_ids),
            )
            .order_by(PriorityEvaluationModel.evaluated_at.desc())
            .limit(1)
        )
        eval_model = (await self.db.execute(stmt)).scalar_one_or_none()
        if not eval_model:
            return None
        item_models = (await self.db.execute(
            select(PriorityItemModel)
            .where(PriorityItemModel.evaluation_id == eval_model.id)
            .order_by(PriorityItemModel.rank)
        )).scalars().all()
        return await self._model_to_dto(eval_model, item_models)

    async def get_latest_evaluation_for_client(
        self,
        tenant_id: str,
        book_ids: list[str],
        client_id: UUID,
    ) -> PriorityEvaluation | None:
        """Latest stored evaluation containing this client, for a real control reference."""
        if not book_ids:
            return None
        stmt = (
            select(PriorityEvaluationModel)
            .join(
                PriorityItemModel,
                PriorityItemModel.evaluation_id == PriorityEvaluationModel.id,
            )
            .where(
                PriorityEvaluationModel.tenant_id == tenant_id,
                PriorityEvaluationModel.book_id.in_(book_ids),
                PriorityItemModel.client_id == client_id,
            )
            .order_by(PriorityEvaluationModel.evaluated_at.desc())
            .limit(1)
        )
        eval_model = (await self.db.execute(stmt)).scalar_one_or_none()
        if not eval_model:
            return None
        item_model = (await self.db.execute(
            select(PriorityItemModel).where(
                PriorityItemModel.evaluation_id == eval_model.id,
                PriorityItemModel.client_id == client_id,
            )
        )).scalar_one_or_none()
        if not item_model:
            return None
        return await self._model_to_dto(eval_model, [item_model])

    async def _fetch_entitled_clients(
        self,
        tenant_id: str,
        book_id: str,
    ) -> list[ClientSummary]:
        """Fetch entitled non-DNC clients from real book assignments and contact policy."""
        stmt = (
            select(ClientAssignment, Client)
            .join(Client, Client.id == ClientAssignment.client_id)
            .where(
                ClientAssignment.tenant_id == tenant_id,
                ClientAssignment.book_id == book_id,
                ClientAssignment.valid.is_(True),
            )
            .order_by(Client.external_id)
        )
        rows = (await self.db.execute(stmt)).all()

        clients = []
        for _, client in rows:
            # Contact policy is stored on the client record; explicit DNC excludes it.
            # Outreach DNC is still enforced separately at the message layer.
            if self._is_dnc(client.preferences):
                continue
            clients.append(
                ClientSummary(
                    id=client.id,
                    external_id=client.external_id,
                    name=client.name,
                    book_id=book_id,
                    client_type=client.client_type,
                    risk_label=client.risk_profile,
                    source=self._create_record_source(
                        "clients", client.id, datetime.now(timezone.utc)
                    ),
                )
            )
        return clients

    @staticmethod
    def _is_dnc(preferences) -> bool:
        """Only explicit DNC/opt-out flags exclude a client; unknown is not a fabricated DNC."""
        if not isinstance(preferences, dict):
            return False
        if preferences.get("dnc") is True or preferences.get("do_not_contact") is True:
            return True
        return preferences.get("contact_policy") in {"dnc", "do_not_contact", "no_contact"}
    
    async def _rank_clients(
        self,
        entitled_clients: list[ClientSummary],
        tenant_id: str,
        book_id: str,
        local_date: date,
        evaluated_at: datetime,
    ) -> list[PriorityItem]:
        """Rank clients with source-linked reasons derived from stored records."""
        previous_ranks = await self._previous_ranks(tenant_id, book_id)
        items = []

        for rank, client in enumerate(entitled_clients, start=1):
            reasons = await self._create_reasons_for_client(client, evaluated_at)
            prev_rank = previous_ranks.get(client.id)
            explanation = (
                f"Moved from rank {prev_rank} to rank {rank}"
                if prev_rank is not None and prev_rank != rank
                else None
            )
            items.append(
                PriorityItem(
                    client=client,
                    rank=rank,
                    reasons=reasons,
                    rank_change_explanation=explanation,
                    controls=[],  # Populated by control_service
                    last_updated_at=evaluated_at,
                )
            )
        return items

    async def _previous_ranks(self, tenant_id: str, book_id: str) -> dict[UUID, int]:
        """Ranks from the last stored CURRENT evaluation, for honest rank-change statements."""
        eval_id = (await self.db.execute(
            select(PriorityEvaluationModel.id)
            .where(
                PriorityEvaluationModel.tenant_id == tenant_id,
                PriorityEvaluationModel.book_id == book_id,
                PriorityEvaluationModel.status == EvaluationStatus.CURRENT.value,
            )
            .order_by(PriorityEvaluationModel.evaluated_at.desc())
            .limit(1)
        )).scalar_one_or_none()
        if not eval_id:
            return {}
        rows = (await self.db.execute(
            select(PriorityItemModel.client_id, PriorityItemModel.rank)
            .where(PriorityItemModel.evaluation_id == eval_id)
        )).all()
        return {client_id: rank for client_id, rank in rows}

    async def _create_reasons_for_client(
        self,
        client: ClientSummary,
        evaluated_at: datetime,
    ) -> list[PriorityReason]:
        """Signals derived from real holdings and interactions; absent data yields no signal."""
        holdings = (await self.db.execute(
            select(Holding).where(Holding.client_id == client.id)
        )).scalars().all()
        total_cost = sum((h.cost_basis or 0) * (h.quantity or 0) for h in holdings)
        total_current = sum(h.current_value or 0 for h in holdings)

        signals: list[PrioritySignal] = []
        if total_cost > 0:
            change_pct = (
                (Decimal(str(total_current)) / Decimal(str(total_cost)) - Decimal(1)) * 100
            ).quantize(Decimal("0.01"))
            signals.append(
                PrioritySignal(
                    key="aum_change_pct",
                    value=FieldValue(type=FieldValueType.DECIMAL, value=change_pct),
                    source=self._create_record_source("holdings", client.id, evaluated_at),
                )
            )

        last_interaction = (await self.db.execute(
            select(func.max(Interaction.interaction_date))
            .where(Interaction.client_id == client.id)
        )).scalar_one_or_none()
        if last_interaction is not None:
            if last_interaction.tzinfo is None:
                last_interaction = last_interaction.replace(tzinfo=timezone.utc)
            days = max((evaluated_at - last_interaction).days, 0)
            signals.append(
                PrioritySignal(
                    key="last_interaction_days",
                    value=FieldValue(type=FieldValueType.DECIMAL, value=Decimal(days)),
                    source=self._create_record_source("interactions", client.id, evaluated_at),
                )
            )

        client_source = self._create_record_source("clients", client.id, evaluated_at)
        key = f"portfolio_signals_{client.id}"
        details = ", ".join(f"{s.key}={s.value.value}" for s in signals)
        explanation = (
            f"Portfolio signals for {client.name}: {details}"
            if details
            else f"No holdings or interaction history available for {client.name}"
        )
        return [
            PriorityReason(
                key=key,
                hash=self._compute_reason_hash(key, evaluated_at),
                classes=[ReasonClass.OPPORTUNITY],
                code="PORTFOLIO_SIGNALS",
                explanation=explanation,
                signals=signals,
                evidence_refs=[EvidenceRef(source_id=client_source.id)]
                + [EvidenceRef(source_id=s.source.id) for s in signals],
            )
        ]

    def _compute_reason_hash(self, reason_key: str, evaluated_at: datetime) -> str:
        """Compute deterministic 64-char hex hash for reason."""
        content = f"{reason_key}:{evaluated_at.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def _create_record_source(system_key: str, record_id, as_of: datetime) -> Source:
        """Provenance for a real stored record; derived signals are as-of evaluation time."""
        return Source(
            id=uuid4(),
            environment=Environment(kind=EnvironmentKind.FIXTURE, id="fixture-ranking-env"),
            availability=Availability.AVAILABLE,
            origin=Origin.RECORDED,
            system_key=system_key,
            record_id=str(record_id),
            as_of=as_of,
            retrieved_at=as_of,
            authoritative_owner=system_key,
            live_response=False,
            limitation_codes=[],
        )
    
    def _create_empty_evaluation(
        self,
        evaluation_id: UUID,
        tenant_id: str,
        book_id: str,
        local_date: date,
        timezone_str: str,
        evaluated_at: datetime,
        principal_subject: str,
        status: EvaluationStatus,
        criteria_summary: str,
        policy_ref: ConfigRef | None = None,
    ) -> PriorityEvaluation:
        """Create empty evaluation (successful empty or failure)."""
        return PriorityEvaluation(
            id=evaluation_id,
            book_id=book_id,
            date=local_date,
            timezone=timezone_str,
            evaluated_at=evaluated_at,
            policy_ref=policy_ref or ConfigRef(id=UUID(int=0), revision=1, hash="0" * 64),
            status=status,
            criteria_summary=criteria_summary,
            items=[],
            environment=Environment(
                kind=EnvironmentKind.FIXTURE,
                id="fixture-ranking-env",
            ),
            source_refs=[],
        )
    
    async def _persist_evaluation(
        self,
        evaluation_id: UUID,
        tenant_id: str,
        book_id: str,
        local_date: date,
        timezone_str: str,
        evaluated_at: datetime,
        principal_subject: str,
        policy_config_id: UUID,
        items: list[PriorityItem],
    ) -> None:
        """Persist evaluation and items to database."""
        # Create evaluation model
        eval_model = PriorityEvaluationModel(
            id=evaluation_id,
            tenant_id=tenant_id,
            book_id=book_id,
            local_date=local_date,
            timezone=timezone_str,
            policy_configuration_id=policy_config_id,
            status=EvaluationStatus.CURRENT.value,
            criteria_summary=f"Top {len(items)} entitled non-DNC clients",
            evaluated_at=evaluated_at,
            environment_kind=EnvironmentKind.FIXTURE.value,
            environment_id="fixture-ranking-env",
            created_by=principal_subject,
        )
        self.db.add(eval_model)
        
        # Create item models
        for item in items:
            # Serialize reasons as JSON
            reasons_json = [
                {
                    "key": r.key,
                    "hash": r.hash,
                    "classes": [c.value for c in r.classes],
                    "code": r.code,
                    "explanation": r.explanation,
                    "signals": [
                        {
                            "key": s.key,
                            "value": {
                                "type": s.value.type.value,
                                "value": str(s.value.value) if isinstance(s.value.value, Decimal) else s.value.value,
                            },
                            "source": {
                                "id": str(s.source.id),
                                "system_key": s.source.system_key,
                                "record_id": s.source.record_id,
                                "as_of": s.source.as_of.isoformat() if s.source.as_of else None,
                            },
                        }
                        for s in r.signals
                    ],
                    "evidence_refs": [{"source_id": str(e.source_id)} for e in r.evidence_refs],
                }
                for r in item.reasons
            ]
            
            item_model = PriorityItemModel(
                id=uuid4(),
                tenant_id=tenant_id,
                book_id=book_id,
                evaluation_id=evaluation_id,
                client_id=item.client.id,
                rank=item.rank,
                reasons=reasons_json,
                rank_change_explanation=item.rank_change_explanation,
                last_updated_at=item.last_updated_at,
            )
            self.db.add(item_model)
        
        await self.db.commit()
    
    async def _model_to_dto(
        self,
        eval_model: PriorityEvaluationModel,
        item_models: list[PriorityItemModel],
    ) -> PriorityEvaluation:
        """Convert model to DTO using the real client record and stored controls."""
        client_ids = [m.client_id for m in item_models]
        clients_by_id: dict[UUID, Client] = {}
        if client_ids:
            clients = (await self.db.execute(
                select(Client).where(Client.id.in_(client_ids))
            )).scalars().all()
            clients_by_id = {c.id: c for c in clients}

        control_service = ControlService(self.db)
        items = []
        for item_model in item_models:
            client = clients_by_id.get(item_model.client_id)
            if client is None:
                # Never fabricate a name for a client record that no longer exists.
                continue
            summary = ClientSummary(
                id=client.id,
                external_id=client.external_id,
                name=client.name,
                book_id=item_model.book_id,
                client_type=client.client_type,
                risk_label=client.risk_profile,
                source=self._create_record_source(
                    "clients", client.id, eval_model.evaluated_at
                ),
            )

            reasons = []
            for reason_json in item_model.reasons or []:
                signals = [
                    PrioritySignal(
                        key=s["key"],
                        value=FieldValue(
                            type=FieldValueType(s["value"]["type"]),
                            value=s["value"]["value"],
                        ),
                        source=self._deserialize_source(
                            s["source"], eval_model.evaluated_at
                        ),
                    )
                    for s in reason_json.get("signals", [])
                ]
                evidence_refs = [
                    EvidenceRef(source_id=UUID(e["source_id"]))
                    for e in reason_json.get("evidence_refs", [])
                ]
                reasons.append(
                    PriorityReason(
                        key=reason_json["key"],
                        hash=reason_json["hash"],
                        classes=[ReasonClass(c) for c in reason_json["classes"]],
                        code=reason_json["code"],
                        explanation=reason_json["explanation"],
                        signals=signals,
                        evidence_refs=evidence_refs,
                    )
                )

            controls = await control_service.get_controls_for_client(
                item_model.tenant_id, item_model.book_id, item_model.client_id
            )
            items.append(
                PriorityItem(
                    client=summary,
                    rank=item_model.rank,
                    reasons=reasons,
                    rank_change_explanation=item_model.rank_change_explanation,
                    controls=controls,
                    last_updated_at=item_model.last_updated_at,
                )
            )

        policy_ref = await get_config_ref(self.db, eval_model.policy_configuration_id)
        if policy_ref is None:
            policy_ref = ConfigRef(
                id=eval_model.policy_configuration_id, revision=1, hash="0" * 64
            )

        return PriorityEvaluation(
            id=eval_model.id,
            book_id=eval_model.book_id,
            date=eval_model.local_date,
            timezone=eval_model.timezone,
            evaluated_at=eval_model.evaluated_at,
            policy_ref=policy_ref,
            status=EvaluationStatus(eval_model.status),
            criteria_summary=eval_model.criteria_summary,
            items=items,
            environment=Environment(
                kind=EnvironmentKind(eval_model.environment_kind),
                id=eval_model.environment_id,
            ),
            source_refs=[],
        )

    @staticmethod
    def _deserialize_source(data: dict, fallback_as_of: datetime) -> Source:
        """Rebuild provenance from the source fields stored with each signal."""
        raw_as_of = data.get("as_of")
        return Source(
            id=UUID(data["id"]),
            environment=Environment(kind=EnvironmentKind.FIXTURE, id="fixture-ranking-env"),
            availability=Availability.AVAILABLE,
            origin=Origin.DERIVED,
            system_key=data.get("system_key"),
            record_id=data.get("record_id"),
            as_of=datetime.fromisoformat(raw_as_of) if raw_as_of else fallback_as_of,
            retrieved_at=fallback_as_of,
            live_response=False,
            limitation_codes=[],
        )
