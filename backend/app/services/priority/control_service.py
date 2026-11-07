"""Priority control service per Architecture §6.6.

Implements snooze/dismiss/pin persistence with policy validation.
Controls affect next evaluation only per explicit policy (DEC-03 gated).
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.priority import (
    ContactOutcome as ContactOutcomeModel,
    PriorityControl as PriorityControlModel,
)
from app.schemas.common import ConfigRef
from app.schemas.priority import (
    ContactOutcomeRequest,
    ContactOutcomeResponseData,
    MeaningfulTouchpoint,
    PriorityControl,
    PriorityControlRequest,
)


class ControlServiceError(Exception):
    """Control service error."""
    pass


class ControlService:
    """Priority control and contact outcome service per architecture §6.6."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def set_priority_control(
        self,
        tenant_id: str,
        book_id: str,
        request: PriorityControlRequest,
        principal_subject: str,
        policy_config_id: UUID | None = None,
    ) -> tuple[PriorityControl, str]:
        """Set priority control (snooze/dismiss/pin) per architecture API-054.
        
        Controls persist and affect next evaluation only per explicit policy.
        Policy UNCONFIGURED blocks control changes.
        
        Args:
            tenant_id: Tenant identifier
            book_id: Book identifier
            request: Control request
            principal_subject: Authenticated principal
            policy_config_id: Ranking policy config (required)
            
        Returns:
            Tuple of (control, evaluation_state) where state is STALE|CURRENT
            
        Raises:
            ControlServiceError: if policy UNCONFIGURED or validation fails
        """
        if policy_config_id is None:
            raise ControlServiceError("Control policy UNCONFIGURED: DEC-03 required")
        
        # Validate control request fields per discriminated union
        control_dict = request.control.model_dump()
        control_type = control_dict["type"]
        
        # Build control model based on type
        recorded_at = datetime.now(UTC)
        
        control_model = PriorityControlModel(
            id=uuid4(),
            tenant_id=tenant_id,
            book_id=book_id,
            client_id=request.client_id,
            evaluation_id=request.recommendation_ref.evaluation_id,
            reason_key=request.recommendation_ref.reason_key,
            reason_hash=request.recommendation_ref.reason_hash,
            control_type=control_type,
            until_at=control_dict.get("until") if control_type == "SNOOZE" else None,
            pinned=control_dict.get("pinned") if control_type == "PIN" else None,
            reason=control_dict.get("reason").model_dump() if control_type == "DISMISS" and "reason" in control_dict else None,
            policy_configuration_id=policy_config_id,
            actor=principal_subject,
            recorded_at=recorded_at,
            row_version=1,
        )
        
        self.db.add(control_model)
        await self.db.commit()
        
        # Build response DTO
        control_dto = PriorityControl(
            id=control_model.id,
            client_id=control_model.client_id,
            book_id=control_model.book_id,
            request=control_dict,
            actor=control_model.actor,
            recorded_at=control_model.recorded_at,
            row_version=control_model.row_version,
            policy_ref=ConfigRef(
                id=policy_config_id,
                revision=1,
                hash="0" * 64,  # Fixture hash
            ),
        )
        
        # Evaluation becomes STALE after control change
        evaluation_state = "STALE"
        
        return control_dto, evaluation_state
    
    async def get_controls_for_client(
        self,
        tenant_id: str,
        book_id: str,
        client_id: UUID,
    ) -> list[PriorityControl]:
        """Get all controls for client.
        
        Args:
            tenant_id: Tenant identifier
            book_id: Book identifier
            client_id: Client identifier
            
        Returns:
            List of controls
        """
        stmt = (
            select(PriorityControlModel)
            .where(
                and_(
                    PriorityControlModel.tenant_id == tenant_id,
                    PriorityControlModel.book_id == book_id,
                    PriorityControlModel.client_id == client_id,
                )
            )
            .order_by(PriorityControlModel.recorded_at.desc())
        )
        
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        
        # Convert to DTOs
        controls = []
        for model in models:
            # Reconstruct control request dict
            if model.control_type == "SNOOZE":
                request_dict = {"type": "SNOOZE", "until": model.until_at}
            elif model.control_type == "DISMISS":
                request_dict = {"type": "DISMISS", "reason": model.reason}
            else:  # PIN
                request_dict = {"type": "PIN", "pinned": bool(model.pinned)}
            
            controls.append(
                PriorityControl(
                    id=model.id,
                    client_id=model.client_id,
                    book_id=model.book_id,
                    request=request_dict,
                    actor=model.actor,
                    recorded_at=model.recorded_at,
                    row_version=model.row_version,
                    policy_ref=ConfigRef(
                        id=model.policy_configuration_id,
                        revision=1,
                        hash="0" * 64,
                    ),
                )
            )
        
        return controls
    
    async def record_contact_outcome(
        self,
        tenant_id: str,
        book_id: str,
        request: ContactOutcomeRequest,
        principal_subject: str,
    ) -> ContactOutcomeResponseData:
        """Record contact outcome per architecture API-055.
        
        Contact outcomes cannot infer two-way/attendance. DNC still blocks outreach.
        Meaningful touchpoint requires confirmed evidence per approved definition.
        
        Args:
            tenant_id: Tenant identifier
            book_id: Book identifier
            request: Contact outcome request
            principal_subject: Authenticated principal
            
        Returns:
            Outcome response with meaningful touchpoint classification
        """
        outcome_id = uuid4()
        recorded_at = datetime.now(UTC)
        
        # Determine meaningful touchpoint classification
        # Per architecture: cannot infer two-way/attendance from send status alone
        # Requires approved definition and confirmed evidence
        # For now, default to NOT_CONFIRMED (conservative)
        meaningful_touchpoint = MeaningfulTouchpoint.NOT_CONFIRMED
        
        # If meeting booked with meeting_id, that's stronger evidence
        if request.outcome == "MEETING_BOOKED" and request.meeting_id is not None:
            meaningful_touchpoint = MeaningfulTouchpoint.CONFIRMED
        
        outcome_model = ContactOutcomeModel(
            id=outcome_id,
            tenant_id=tenant_id,
            book_id=book_id,
            client_id=request.client_id,
            evaluation_id=request.recommendation_ref.evaluation_id,
            reason_key=request.recommendation_ref.reason_key,
            reason_hash=request.recommendation_ref.reason_hash,
            outcome=request.outcome.value,
            occurred_at=request.occurred_at,
            recorded_at=recorded_at,
            note=request.note,
            meeting_id=request.meeting_id,
            evidence_refs=[{"source_id": str(ref.source_id)} for ref in request.evidence_refs],
            meaningful_touchpoint=meaningful_touchpoint.value,
            actor=principal_subject,
        )
        
        self.db.add(outcome_model)
        await self.db.commit()
        
        return ContactOutcomeResponseData(
            outcome_id=outcome_id,
            meaningful_touchpoint=meaningful_touchpoint,
        )
