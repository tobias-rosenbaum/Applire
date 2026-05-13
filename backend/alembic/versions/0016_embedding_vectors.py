"""Add embedding vectors to job_analyses and master_profiles

Revision ID: 0016
Revises: 0015
Create Date: 2026-04-07

Notes:
- On PostgreSQL: enables the pgvector extension and adds VECTOR(1024) columns.
- On SQLite: adds nullable TEXT columns (no pgvector, embeddings always NULL).
  The noop embedding provider is the Community default, so SQLite test runs
  are unaffected — the column exists but is never populated.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgresql():
        # Enable pgvector extension (idempotent).
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # Add as text first, then ALTER to the VECTOR type so Alembic's column
        # introspection doesn't need to know the pgvector dialect type at import time.
        op.add_column("job_analyses", sa.Column("embedding", sa.Text(), nullable=True))
        op.execute(
            "ALTER TABLE job_analyses "
            "ALTER COLUMN embedding TYPE vector(1024) "
            "USING embedding::vector(1024)"
        )

        op.add_column("master_profiles", sa.Column("embedding", sa.Text(), nullable=True))
        op.execute(
            "ALTER TABLE master_profiles "
            "ALTER COLUMN embedding TYPE vector(1024) "
            "USING embedding::vector(1024)"
        )
    else:
        # SQLite: add nullable TEXT columns so the ORM mapping is satisfied.
        # Embeddings are never stored here (noop provider returns zero-vectors
        # which are not persisted on SQLite).
        op.add_column("job_analyses", sa.Column("embedding", sa.Text(), nullable=True))
        op.add_column("master_profiles", sa.Column("embedding", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("master_profiles", "embedding")
    op.drop_column("job_analyses", "embedding")
    # Leave the pgvector extension in place — other tables may depend on it.
