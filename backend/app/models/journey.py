"""Wealth-sales journey tables. Client id is the demo-client universe (PLT-01)."""
from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


def _now():
    return datetime.now(UTC)


class JourneySignal(Base):
    __tablename__ = "journey_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False, index=True)
    kind = Column(String(40), nullable=False)
    summary = Column(Text, nullable=False)
    source = Column(String(80), nullable=False, default="journey")
    as_of = Column(Date, nullable=False)
    active = Column(Boolean, default=True, nullable=False)


class JourneyLeadControl(Base):
    __tablename__ = "journey_lead_controls"

    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), primary_key=True)
    state = Column(String(20), nullable=False)  # PIN, SNOOZE, DISMISS
    updated_at = Column(DateTime(timezone=True), default=_now)


class JourneyOpportunity(Base):
    __tablename__ = "journey_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    stage = Column(String(40), nullable=False, default="ACTIONABLE")
    source = Column(String(40), nullable=False, default="SIGNAL")
    value_usd = Column(Float, default=0)
    probability_pct = Column(Float, default=20)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now)


class JourneyInvestorProfile(Base):
    __tablename__ = "journey_investor_profiles"

    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), primary_key=True)
    rpq_band = Column(String(40))
    rpq_score = Column(Integer)
    rpq_answers = Column(JSONB, default=dict)
    cka_passed = Column(Boolean, default=False)
    car_status = Column(String(40), default="PENDING")
    investor_status = Column(String(40), default="RETAIL")
    accreditation_evidence = Column(String(200))
    expiry_date = Column(Date)
    vulnerable = Column(Boolean, default=False)
    high_risk_segment = Column(Boolean, default=False)
    cross_border_restricted = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=_now)


class JourneyFinancialProfile(Base):
    __tablename__ = "journey_financial_profiles"

    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), primary_key=True)
    annual_income_band = Column(String(40))
    investable_assets_band = Column(String(40))
    liquidity_need = Column(String(40))
    investment_objective = Column(String(80))
    confirmed_at = Column(DateTime(timezone=True))
    confirmed_by = Column(String(120))
    version = Column(Integer, default=1, nullable=False)


class JourneyGoal(Base):
    __tablename__ = "journey_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    target_usd = Column(Float, nullable=False)
    target_date = Column(Date)
    monthly_contribution_usd = Column(Float, default=0)
    current_usd = Column(Float, default=0)
    status = Column(String(30), default="OPEN")
    product_tags = Column(JSONB, default=list)


class JourneyDocument(Base):
    __tablename__ = "journey_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False, index=True)
    document_type = Column(String(40), nullable=False)
    file_name = Column(String(200), nullable=False)
    note = Column(Text)
    expires_on = Column(Date)
    uploaded_at = Column(DateTime(timezone=True), default=_now)


class JourneyTransaction(Base):
    __tablename__ = "journey_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    txn_type = Column(String(40), nullable=False)
    description = Column(String(200), nullable=False)
    amount_usd = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    source = Column(String(80), default="SYNTHETIC_DEMO_DATA")


class JourneyCart(Base):
    __tablename__ = "journey_carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False, index=True)
    status = Column(String(40), nullable=False, default="DRAFT")
    signed_by = Column(String(120))
    signed_at = Column(DateTime(timezone=True))
    suitability_rating = Column(String(20))
    maker = Column(String(120))
    created_at = Column(DateTime(timezone=True), default=_now)


class JourneyCartItem(Base):
    __tablename__ = "journey_cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("journey_carts.id"), nullable=False, index=True)
    product_id = Column(String(80), nullable=False)
    order_type = Column(String(20), nullable=False)
    amount_usd = Column(Float, nullable=False)
    side = Column(String(20), default="BUY")  # BUY, SELL, SWITCH
    discount_pct = Column(Float, default=0)
    goal_id = Column(UUID(as_uuid=True), nullable=True)


class JourneyApproval(Base):
    __tablename__ = "journey_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("journey_carts.id"), nullable=False, unique=True)
    maker = Column(String(120), nullable=False)
    status = Column(String(40), nullable=False)  # AUTO_APPROVED, PENDING, APPROVED, REJECTED
    checker = Column(String(120))
    checker_role = Column(String(40))
    reason = Column(Text)
    decided_at = Column(DateTime(timezone=True))


class JourneyHandoff(Base):
    __tablename__ = "journey_handoffs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("journey_carts.id"), nullable=False, unique=True)
    oms_order_id = Column(String(80), nullable=False)
    status = Column(String(40), nullable=False, default="ACCEPTED")
    payload_hash = Column(String(64), nullable=False)
    label = Column(String(80), default="DEMO SINK — not submitted")
    updated_at = Column(DateTime(timezone=True), default=_now)


class JourneyNotification(Base):
    __tablename__ = "journey_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=True, index=True)
    kind = Column(String(40), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    href = Column(String(200))
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)


class JourneyEvent(Base):
    __tablename__ = "journey_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    stage = Column(String(20), nullable=False)
    event = Column(String(60), nullable=False)
    client_id = Column(UUID(as_uuid=True), nullable=True)
    actor = Column(String(120))
    detail = Column(JSONB, default=dict)
    occurred_at = Column(DateTime(timezone=True), default=_now)


class JourneyCohort(Base):
    __tablename__ = "journey_cohorts"
    __table_args__ = (UniqueConstraint("name"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(80), nullable=False)
    filters = Column(JSONB, default=dict)
