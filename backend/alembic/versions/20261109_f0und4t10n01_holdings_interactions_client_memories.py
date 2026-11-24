"""Create holdings, interactions and client_memories.

Revision ID: f0und4t10n01
Revises: m3m0ry0001

These three tables exist as ORM models but were never migrated, so a fresh
database 500s on portfolio/brief/memory paths. Each create is guarded by an
inspector check so the migration is safe on databases that already have some
of them (e.g. bootstrapped with Base.metadata.create_all).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "f0und4t10n01"
down_revision: Union[str, None] = "m3m0ry0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_tables() -> set[str]:
    # Offline (--sql) mode has no live connection to inspect; assume none exist
    # so upgrade still emits all CREATE statements.
    if context.is_offline_mode():
        return set()
    return set(inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    existing = _existing_tables()

    if "holdings" not in existing:
        op.create_table(
            "holdings",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("symbol", sa.String(), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=True),
            sa.Column("cost_basis", sa.Float(), nullable=True),
            sa.Column("current_value", sa.Float(), nullable=True),
            sa.Column("asset_class", sa.String(), nullable=True),
            sa.Column("source_kind", sa.String(), nullable=True),
            sa.Column("as_of", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "interactions" not in existing:
        op.create_table(
            "interactions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("interaction_date", sa.DateTime(), nullable=False),
            sa.Column("interaction_type", sa.String(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("preferences_extracted", sa.JSON(), nullable=True),
            sa.Column("action_items", sa.JSON(), nullable=True),
            sa.Column("recording_consent", sa.Boolean(), nullable=True),
            sa.Column("consent_method", sa.String(), nullable=True),
            sa.Column("source_kind", sa.String(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "client_memories" not in existing:
        op.create_table(
            "client_memories",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("memory_type", sa.String(), nullable=False),
            sa.Column("key", sa.String(), nullable=False),
            sa.Column("value", sa.Text(), nullable=True),
            # "metadata" is reserved by SQLAlchemy's declarative base.
            sa.Column("extra_metadata", sa.JSON(), nullable=True),
            sa.Column("confidence", sa.String(), nullable=True),
            sa.Column("source", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    existing = _existing_tables()
    for table in ("client_memories", "interactions", "holdings"):
        if context.is_offline_mode() or table in existing:
            op.drop_table(table)
