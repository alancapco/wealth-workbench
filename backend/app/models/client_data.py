"""Demo client models — replaces HubSpot as local data source."""
from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DemoClient(Base):
    __tablename__ = "demo_clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    # Identity
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    # Demographics
    city = Column(String(100))
    country = Column(String(100))
    ethnicity = Column(String(100))
    religion = Column(String(50))
    language_preference = Column(String(50))
    # Wealth profile
    aum_usd_millions = Column(Float)
    client_segment = Column(String(50))
    risk_profile = Column(String(50))
    portfolio_type = Column(String(50))
    shariah_compliant = Column(Boolean, default=False)
    # Family office
    family_office_name = Column(String(200))
    family_role = Column(String(50))
    family_patriarch_email = Column(String(255))
    # Status
    tag = Column(String(50), default="capcodemo")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    portfolio_holdings = relationship("ClientPortfolioHolding", back_populates="client", cascade="all, delete-orphan")
    financial_plans = relationship("ClientFinancialPlan", back_populates="client", cascade="all, delete-orphan")
    conversations = relationship("ClientConversation", back_populates="client", cascade="all, delete-orphan")
    suitability = relationship("ClientSuitabilityProfile", back_populates="client", uselist=False, cascade="all, delete-orphan")


class ClientPortfolioHolding(Base):
    __tablename__ = "client_portfolio_holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False)
    asset_class = Column(String(100))
    asset_name = Column(String(200))
    ticker = Column(String(20))
    value_usd_millions = Column(Float)
    allocation_pct = Column(Float)
    unrealized_gain_pct = Column(Float)
    currency = Column(String(10))
    is_shariah_compliant = Column(Boolean, default=False)
    as_of_date = Column(Date)

    client = relationship("DemoClient", back_populates="portfolio_holdings")


class ClientFinancialPlan(Base):
    __tablename__ = "client_financial_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False)
    plan_type = Column(String(100))
    goal_description = Column(Text)
    target_amount_usd_millions = Column(Float)
    target_date = Column(Date)
    current_progress_pct = Column(Float)
    status = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    client = relationship("DemoClient", back_populates="financial_plans")


class ClientConversation(Base):
    __tablename__ = "client_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False)
    conversation_date = Column(Date, nullable=False)
    channel = Column(String(50))
    summary = Column(Text)
    sentiment = Column(String(20))
    action_items = Column(JSONB)
    next_steps = Column(Text)
    rm_notes = Column(Text)

    client = relationship("DemoClient", back_populates="conversations")


class ClientSuitabilityProfile(Base):
    __tablename__ = "client_suitability_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("demo_clients.id"), nullable=False, unique=True)
    risk_tolerance = Column(String(50))
    investment_horizon_years = Column(Integer)
    liquidity_needs = Column(String(50))
    esg_preference = Column(Boolean, default=False)
    shariah_preference = Column(Boolean, default=False)
    max_single_stock_pct = Column(Float)
    profile_date = Column(Date)
    expiry_date = Column(Date)
    is_expired = Column(Boolean, default=False)

    client = relationship("DemoClient", back_populates="suitability")
