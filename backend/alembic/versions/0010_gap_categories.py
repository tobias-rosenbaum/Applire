"""Gap analysis: A/B/C categories + float match_score; interview_sessions nullable gap_analysis_id

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-15

Changes:
  gap_analyses:
    - match_score: INTEGER → FLOAT (USING match_score / 100.0)
    - ADD category_a  JSONB NOT NULL DEFAULT '[]'
    - ADD category_b  JSONB NOT NULL DEFAULT '[]'
    - ADD category_c  JSONB NOT NULL DEFAULT '[]'

  interview_sessions:
    - gap_analysis_id: NOT NULL → NULL (decouple session creation from gap analysis)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- gap_analyses: match_score INTEGER → FLOAT ---
    op.alter_column(
        "gap_analyses",
        "match_score",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        postgresql_using="match_score / 100.0",
        nullable=False,
    )

    # --- gap_analyses: add A/B/C category columns ---
    op.add_column(
        "gap_analyses",
        sa.Column("category_a", JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "gap_analyses",
        sa.Column("category_b", JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "gap_analyses",
        sa.Column("category_c", JSONB(), nullable=False, server_default="[]"),
    )

    # --- interview_sessions: gap_analysis_id → nullable ---
    op.alter_column(
        "interview_sessions",
        "gap_analysis_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    # Restore interview_sessions.gap_analysis_id to NOT NULL
    # (will fail if any rows have NULL — acceptable for downgrade)
    op.alter_column(
        "interview_sessions",
        "gap_analysis_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    # Drop category columns
    op.drop_column("gap_analyses", "category_c")
    op.drop_column("gap_analyses", "category_b")
    op.drop_column("gap_analyses", "category_a")

    # Restore match_score to INTEGER (truncates fractional part)
    op.alter_column(
        "gap_analyses",
        "match_score",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        postgresql_using="ROUND(match_score * 100)::INTEGER",
        nullable=False,
    )
