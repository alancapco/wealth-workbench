"""Journey tables and additive client columns.

Revision ID: j0urn3y0001
Revises: f0und4t10n01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "j0urn3y0001"
down_revision: Union[str, None] = "f0und4t10n01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_tables() -> set[str]:
    if context.is_offline_mode():
        return set()
    return set(inspect(op.get_bind()).get_table_names())


def _uuid_pk():
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def _client_fk(nullable=False):
    return sa.Column(
        "client_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("demo_clients.id"),
        nullable=nullable,
    )


def upgrade() -> None:
    existing = _existing_tables()
    if "clients" in existing and not context.is_offline_mode():
        present = {col["name"] for col in inspect(op.get_bind()).get_columns("clients")}
        additions = {
            "phone": sa.Column("phone", sa.String()),
            "aum": sa.Column("aum", sa.Float()),
            "currency": sa.Column("currency", sa.String()),
            "client_type": sa.Column("client_type", sa.String()),
            "region": sa.Column("region", sa.String()),
            "risk_profile": sa.Column("risk_profile", sa.String()),
            "is_family_office": sa.Column("is_family_office", sa.Boolean()),
            "shariah_compliant": sa.Column("shariah_compliant", sa.Boolean()),
        }
        for name, column in additions.items():
            if name not in present:
                op.add_column("clients", column)

    if "journey_signals" not in existing:
        op.create_table(
            "journey_signals",
            _uuid_pk(),
            _client_fk(),
            sa.Column("kind", sa.String(40), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("source", sa.String(80), nullable=False),
            sa.Column("as_of", sa.Date(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False),
        )
    if "journey_lead_controls" not in existing:
        op.create_table(
            "journey_lead_controls",
            sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("demo_clients.id"), primary_key=True),
            sa.Column("state", sa.String(20), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        )
    if "journey_opportunities" not in existing:
        op.create_table(
            "journey_opportunities",
            _uuid_pk(),
            _client_fk(),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("stage", sa.String(40), nullable=False),
            sa.Column("source", sa.String(40), nullable=False),
            sa.Column("value_usd", sa.Float()),
            sa.Column("probability_pct", sa.Float()),
            sa.Column("created_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        )
    if "journey_investor_profiles" not in existing:
        op.create_table(
            "journey_investor_profiles",
            sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("demo_clients.id"), primary_key=True),
            sa.Column("rpq_band", sa.String(40)),
            sa.Column("rpq_score", sa.Integer()),
            sa.Column("rpq_answers", postgresql.JSONB()),
            sa.Column("cka_passed", sa.Boolean()),
            sa.Column("car_status", sa.String(40)),
            sa.Column("investor_status", sa.String(40)),
            sa.Column("accreditation_evidence", sa.String(200)),
            sa.Column("expiry_date", sa.Date()),
            sa.Column("vulnerable", sa.Boolean()),
            sa.Column("high_risk_segment", sa.Boolean()),
            sa.Column("cross_border_restricted", sa.Boolean()),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        )
    if "journey_financial_profiles" not in existing:
        op.create_table(
            "journey_financial_profiles",
            sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("demo_clients.id"), primary_key=True),
            sa.Column("annual_income_band", sa.String(40)),
            sa.Column("investable_assets_band", sa.String(40)),
            sa.Column("liquidity_need", sa.String(40)),
            sa.Column("investment_objective", sa.String(80)),
            sa.Column("confirmed_at", sa.DateTime(timezone=True)),
            sa.Column("confirmed_by", sa.String(120)),
            sa.Column("version", sa.Integer(), nullable=False),
        )
    if "journey_goals" not in existing:
        op.create_table(
            "journey_goals",
            _uuid_pk(),
            _client_fk(),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("target_usd", sa.Float(), nullable=False),
            sa.Column("target_date", sa.Date()),
            sa.Column("monthly_contribution_usd", sa.Float()),
            sa.Column("current_usd", sa.Float()),
            sa.Column("status", sa.String(30)),
            sa.Column("product_tags", postgresql.JSONB()),
        )
    if "journey_documents" not in existing:
        op.create_table(
            "journey_documents",
            _uuid_pk(),
            _client_fk(),
            sa.Column("document_type", sa.String(40), nullable=False),
            sa.Column("file_name", sa.String(200), nullable=False),
            sa.Column("note", sa.Text()),
            sa.Column("expires_on", sa.Date()),
            sa.Column("uploaded_at", sa.DateTime(timezone=True)),
        )
    if "journey_transactions" not in existing:
        op.create_table(
            "journey_transactions",
            _uuid_pk(),
            _client_fk(),
            sa.Column("trade_date", sa.Date(), nullable=False),
            sa.Column("txn_type", sa.String(40), nullable=False),
            sa.Column("description", sa.String(200), nullable=False),
            sa.Column("amount_usd", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(10)),
            sa.Column("source", sa.String(80)),
        )
    if "journey_carts" not in existing:
        op.create_table(
            "journey_carts",
            _uuid_pk(),
            _client_fk(),
            sa.Column("status", sa.String(40), nullable=False),
            sa.Column("signed_by", sa.String(120)),
            sa.Column("signed_at", sa.DateTime(timezone=True)),
            sa.Column("suitability_rating", sa.String(20)),
            sa.Column("maker", sa.String(120)),
            sa.Column("created_at", sa.DateTime(timezone=True)),
        )
    if "journey_cart_items" not in existing:
        op.create_table(
            "journey_cart_items",
            _uuid_pk(),
            sa.Column("cart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journey_carts.id"), nullable=False),
            sa.Column("product_id", sa.String(80), nullable=False),
            sa.Column("order_type", sa.String(20), nullable=False),
            sa.Column("amount_usd", sa.Float(), nullable=False),
            sa.Column("side", sa.String(20)),
            sa.Column("discount_pct", sa.Float()),
            sa.Column("goal_id", postgresql.UUID(as_uuid=True)),
        )
    if "journey_approvals" not in existing:
        op.create_table(
            "journey_approvals",
            _uuid_pk(),
            sa.Column("cart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journey_carts.id"), nullable=False),
            sa.Column("maker", sa.String(120), nullable=False),
            sa.Column("status", sa.String(40), nullable=False),
            sa.Column("checker", sa.String(120)),
            sa.Column("checker_role", sa.String(40)),
            sa.Column("reason", sa.Text()),
            sa.Column("decided_at", sa.DateTime(timezone=True)),
            sa.UniqueConstraint("cart_id"),
        )
    if "journey_handoffs" not in existing:
        op.create_table(
            "journey_handoffs",
            _uuid_pk(),
            sa.Column("cart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journey_carts.id"), nullable=False),
            sa.Column("oms_order_id", sa.String(80), nullable=False),
            sa.Column("status", sa.String(40), nullable=False),
            sa.Column("payload_hash", sa.String(64), nullable=False),
            sa.Column("label", sa.String(80)),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
            sa.UniqueConstraint("cart_id"),
        )
    if "journey_notifications" not in existing:
        op.create_table(
            "journey_notifications",
            _uuid_pk(),
            _client_fk(nullable=True),
            sa.Column("kind", sa.String(40), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("href", sa.String(200)),
            sa.Column("read", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True)),
        )
    if "journey_events" not in existing:
        op.create_table(
            "journey_events",
            _uuid_pk(),
            sa.Column("stage", sa.String(20), nullable=False),
            sa.Column("event", sa.String(60), nullable=False),
            sa.Column("client_id", postgresql.UUID(as_uuid=True)),
            sa.Column("actor", sa.String(120)),
            sa.Column("detail", postgresql.JSONB()),
            sa.Column("occurred_at", sa.DateTime(timezone=True)),
        )
    if "journey_cohorts" not in existing:
        op.create_table(
            "journey_cohorts",
            _uuid_pk(),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("filters", postgresql.JSONB()),
            sa.UniqueConstraint("name"),
        )


def downgrade() -> None:
    for name in (
        "journey_cohorts",
        "journey_events",
        "journey_notifications",
        "journey_handoffs",
        "journey_approvals",
        "journey_cart_items",
        "journey_carts",
        "journey_transactions",
        "journey_documents",
        "journey_goals",
        "journey_financial_profiles",
        "journey_investor_profiles",
        "journey_opportunities",
        "journey_lead_controls",
        "journey_signals",
    ):
        op.drop_table(name)
