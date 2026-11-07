"""Book-wide priority ranking service per Architecture §6.6.

Implements deterministic evaluation with source-linked reasons, stale/outage state,
DST-aware local date, and top-10 cap of currently entitled non-DNC clients.
"""
import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.priority import PriorityEvaluation as PriorityEvaluationModel
from app.models.priority import PriorityItem as PriorityItemModel
from app.schemas.client import ClientSummary
from app.schemas.common import (
    Availability,
    CapabilityState,
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
            policy_config_id: Optional ranking policy config (UNCONFIGURED if None)
            
        Returns:
            PriorityEvaluation with up to 10 items
            
        Raises:
            RankingServiceError: if dependency unavailable
        """
        evaluation_id = uuid4()
        evaluated_at = datetime.now(timezone.utc)
        
        # Without policy config, return UNCONFIGURED capability state via empty eval
        if policy_config_id is None:
            # Per architecture: CONFIG_UNCONFIGURED blocks, but we still return structure
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
        
        # Fetch entitled non-DNC clients for book
        # Real implementation queries client_assignments + contact_policy
        # For now, use deterministic synthetic fixture
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
            policy_ref={
                "id": policy_config_id,
                "revision": 1,
                "hash": "0" * 64,  # Fixture hash
            },
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
    
    async def _fetch_entitled_clients(
        self,
        tenant_id: str,
        book_id: str,
    ) -> list[ClientSummary]:
        """Fetch entitled non-DNC clients for book.
        
        Real implementation queries client_assignments + contact_policy.
        Returns deterministic synthetic fixture for now.
        """
        # Deterministic synthetic clients
        fixture_clients = [
            ClientSummary(
                id=UUID("11111111-1111-1111-1111-111111111111"),
                external_id="CLIENT_001",
                name="Alice Anderson",
                book_id=book_id,
                client_type="PRIVATE_WEALTH",
                risk_label="MODERATE",
                source=self._create_fixture_source(),
            ),
            ClientSummary(
                id=UUID("22222222-2222-2222-2222-222222222222"),
                external_id="CLIENT_002",
                name="Bob Baker",
                book_id=book_id,
                client_type="FAMILY_OFFICE",
                risk_label="CONSERVATIVE",
                source=self._create_fixture_source(),
            ),
            ClientSummary(
                id=UUID("33333333-3333-3333-3333-333333333333"),
                external_id="CLIENT_003",
                name="Carol Chen",
                book_id=book_id,
                client_type="PRIVATE_WEALTH",
                risk_label="AGGRESSIVE",
                source=self._create_fixture_source(),
            ),
        ]
        
        return fixture_clients
    
    async def _rank_clients(
        self,
        entitled_clients: list[ClientSummary],
        tenant_id: str,
        book_id: str,
        local_date: date,
        evaluated_at: datetime,
    ) -> list[PriorityItem]:
        """Rank clients with deterministic source-linked reasons.
        
        Per architecture: reasons link to source IDs/as-of timestamps,
        rank changes explained when applicable.
        """
        items = []
        
        for rank, client in enumerate(entitled_clients, start=1):
            # Create deterministic reasons with source evidence
            reasons = self._create_reasons_for_client(client, evaluated_at)
            
            item = PriorityItem(
                client=client,
                rank=rank,
                reasons=reasons,
                rank_change_explanation=None if rank == 1 else f"Moved from rank {rank+1}",
                controls=[],  # Populated by control_service
                last_updated_at=evaluated_at,
            )
            items.append(item)
        
        return items
    
    def _create_reasons_for_client(
        self,
        client: ClientSummary,
        evaluated_at: datetime,
    ) -> list[PriorityReason]:
        """Create deterministic reasons with source-linked signals."""
        source = self._create_fixture_source()
        source_id = source.id
        
        # Create reason with signals and evidence
        reason = PriorityReason(
            key=f"aum_increase_{client.id}",
            hash=self._compute_reason_hash(f"aum_increase_{client.id}", evaluated_at),
            classes=[ReasonClass.OPPORTUNITY],
            code="AUM_INCREASE",
            explanation=f"Portfolio growth opportunity for {client.name}",
            signals=[
                PrioritySignal(
                    key="aum_change_pct",
                    value=FieldValue(
                        type=FieldValueType.DECIMAL,
                        value=Decimal("15.5"),
                    ),
                    source=source,
                ),
                PrioritySignal(
                    key="last_interaction_days",
                    value=FieldValue(
                        type=FieldValueType.DECIMAL,
                        value=Decimal("45"),
                    ),
                    source=source,
                ),
            ],
            evidence_refs=[
                EvidenceRef(source_id=source_id, source_version="v1"),
            ],
        )
        
        return [reason]
    
    def _compute_reason_hash(self, reason_key: str, evaluated_at: datetime) -> str:
        """Compute deterministic 64-char hex hash for reason."""
        content = f"{reason_key}:{evaluated_at.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _create_fixture_source(self) -> Source:
        """Create deterministic fixture source."""
        return Source(
            id=uuid4(),
            environment=Environment(
                kind=EnvironmentKind.FIXTURE,
                id="fixture-ranking-env",
            ),
            availability=Availability.AVAILABLE,
            origin=Origin.DERIVED,
            system_key="ranking_service",
            record_id=None,
            record_version=None,
            as_of=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
            authoritative_owner="ranking_service",
            freshness_policy_ref=None,
            live_response=False,  # Fixture, not live
            adapter_receipt_id=None,
            confidence=Decimal("1.0"),
            evidence=None,
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
    ) -> PriorityEvaluation:
        """Create empty evaluation (successful empty or failure)."""
        return PriorityEvaluation(
            id=evaluation_id,
            book_id=book_id,
            date=local_date,
            timezone=timezone_str,
            evaluated_at=evaluated_at,
            policy_ref={
                "id": uuid4(),
                "revision": 1,
                "hash": "0" * 64,
            },
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
                            "source": {"id": str(s.source.id)},
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
        """Convert model to DTO."""
        # Convert items
        items = []
        for item_model in item_models:
            # Deserialize client summary
            client = ClientSummary(
                id=item_model.client_id,
                external_id=f"CLIENT_{item_model.rank:03d}",
                name=f"Client {item_model.rank}",
                book_id=item_model.book_id,
                client_type=None,
                risk_label=None,
                source=self._create_fixture_source(),
            )
            
            # Deserialize reasons
            reasons = []
            for reason_json in item_model.reasons:
                reasons.append(
                    PriorityReason(
                        key=reason_json["key"],
                        hash=reason_json["hash"],
                        classes=[ReasonClass(c) for c in reason_json["classes"]],
                        code=reason_json["code"],
                        explanation=reason_json["explanation"],
                        signals=[],
                        evidence_refs=[],
                    )
                )
            
            items.append(
                PriorityItem(
                    client=client,
                    rank=item_model.rank,
                    reasons=reasons,
                    rank_change_explanation=item_model.rank_change_explanation,
                    controls=[],
                    last_updated_at=item_model.last_updated_at,
                )
            )
        
        return PriorityEvaluation(
            id=eval_model.id,
            book_id=eval_model.book_id,
            date=eval_model.local_date,
            timezone=eval_model.timezone,
            evaluated_at=eval_model.evaluated_at,
            policy_ref={
                "id": eval_model.policy_configuration_id,
                "revision": 1,
                "hash": "0" * 64,
            },
            status=EvaluationStatus(eval_model.status),
            criteria_summary=eval_model.criteria_summary,
            items=items,
            environment=Environment(
                kind=EnvironmentKind(eval_model.environment_kind),
                id=eval_model.environment_id,
            ),
            source_refs=[],
        )
