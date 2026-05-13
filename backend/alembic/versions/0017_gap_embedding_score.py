"""Add embedding_similarity_score to gap_analyses

Revision ID: 0017
Revises: 0016
Create Date: 2026-04-07

Notes:
- Adds nullable FLOAT column embedding_similarity_score to gap_analyses.
- Runs on both PostgreSQL and SQLite (standard Float, no pgvector dependency).
- NULL means no embedding similarity has been computed yet (noop provider or pre-migration rows).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "gap_analyses",
        sa.Column("embedding_similarity_score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("gap_analyses", "embedding_similarity_score")
