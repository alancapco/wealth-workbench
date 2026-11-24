"""aaoifi_knowledge_base

Revision ID: a1b2c3d4e5f6
Revises: df83fca46282
Create Date: 2026-11-08 12:30:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'df83fca46282'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The VECTOR column below needs the type to exist before CREATE TABLE runs;
    # creating the extension afterwards used to break fresh-database upgrades.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'aaoifi_standards',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('authority', sa.Text(), nullable=False),
        sa.Column('standard_number', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('edition', sa.Text(), nullable=False),
        sa.Column('source_checksum', sa.Text(), nullable=False),
        sa.Column('approval_status', sa.Text(), nullable=False, server_default='draft'),
        sa.Column('language', sa.Text(), nullable=False, server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("approval_status IN ('draft','approved','rejected')"),
        sa.UniqueConstraint('authority', 'standard_number', 'edition', 'language', 'source_checksum'),
    )

    op.create_table(
        'aaoifi_clauses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('standard_id', sa.UUID(), nullable=False),
        sa.Column('clause_id', sa.Text(), nullable=False),
        sa.Column('parent_clause_id', sa.Text(), nullable=True),
        sa.Column('breadcrumb', sa.Text(), nullable=False, server_default=''),
        sa.Column('verbatim_text', sa.Text(), nullable=False),
        sa.Column('embedding_text', sa.Text(), nullable=False),
        sa.Column('source_pdf_page_start', sa.Integer(), nullable=False),
        sa.Column('source_pdf_page_end', sa.Integer(), nullable=False),
        sa.Column('printed_page_start', sa.Integer(), nullable=False),
        sa.Column('printed_page_end', sa.Integer(), nullable=False),
        sa.Column('language', sa.Text(), nullable=False, server_default='en'),
        sa.Column('approval_status', sa.Text(), nullable=False, server_default='draft'),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['standard_id'], ['aaoifi_standards.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("approval_status IN ('draft','approved','rejected')"),
        sa.UniqueConstraint('standard_id', 'clause_id'),
    )

    op.create_index(
        'ix_aaoifi_clauses_standard_approval',
        'aaoifi_clauses',
        ['standard_id', 'approval_status'],
    )
    op.create_index(
        'ix_aaoifi_clauses_approval',
        'aaoifi_clauses',
        ['approval_status'],
    )

    # GIN index for full-text search using tsvector generated column
    op.execute(
        "CREATE INDEX ix_aaoifi_clauses_embedding_text_tsv "
        "ON aaoifi_clauses USING gin (to_tsvector('english', embedding_text))"
    )

    # ivfflat index for pgvector cosine similarity
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_aaoifi_clauses_embedding_ivfflat "
        "ON aaoifi_clauses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_aaoifi_clauses_embedding_ivfflat")
    op.execute("DROP INDEX IF EXISTS ix_aaoifi_clauses_embedding_text_tsv")
    op.drop_index('ix_aaoifi_clauses_approval', table_name='aaoifi_clauses')
    op.drop_index('ix_aaoifi_clauses_standard_approval', table_name='aaoifi_clauses')
    op.drop_table('aaoifi_clauses')
    op.drop_table('aaoifi_standards')
