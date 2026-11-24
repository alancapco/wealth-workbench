"""Add client_memory_records for the client memory proposal workflow.

Revision ID: m3m0ry0001
Revises: a1b2c3d4e5f6
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "m3m0ry0001"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_memory_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_type", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Text(), nullable=True),
        sa.Column("proposed_by", sa.Text(), nullable=True),
        sa.Column("proposed_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.Text(), nullable=True),
        sa.Column("reviewed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "entry_type IN ('PREFERENCE', 'FACT', 'CONSTRAINT', 'GOAL')",
            name="ck_memory_record_type",
        ),
        sa.CheckConstraint(
            "state IN ('NEEDS_REVIEW', 'CONFIRMED', 'REJECTED')",
            name="ck_memory_record_state",
        ),
    )
    op.create_index(
        "ix_memory_record_client_state",
        "client_memory_records",
        ["tenant_id", "client_id", "state", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_memory_record_client_state", table_name="client_memory_records")
    op.drop_table("client_memory_records")
