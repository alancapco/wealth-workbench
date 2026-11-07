"""Create briefs and audit_logs tables

Revision ID: 001
Revises:
Create Date: 2024-11-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_briefs_audit'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create briefs table
    op.create_table('briefs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('sections', postgresql.JSON(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('actor', sa.String(), nullable=False),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_briefs_client_id', 'briefs', ['client_id'])
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])


def downgrade():
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    op.drop_index('ix_briefs_client_id', table_name='briefs')
    op.drop_table('audit_logs')
    op.drop_table('briefs')
