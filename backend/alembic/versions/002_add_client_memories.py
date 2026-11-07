"""Add client_memories table

Revision ID: 002
Revises: 001_add_briefs_audit
Create Date: 2024-11-07 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_add_client_memories'
down_revision = '001_add_briefs_audit'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('client_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('memory_type', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('confidence', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_client_memories_client_id', 'client_memories', ['client_id'])
    op.create_index('ix_client_memories_type', 'client_memories', ['memory_type'])


def downgrade():
    op.drop_index('ix_client_memories_type', table_name='client_memories')
    op.drop_index('ix_client_memories_client_id', table_name='client_memories')
    op.drop_table('client_memories')
