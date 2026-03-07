"""Gap analyses table

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gap_analyses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_analysis_id", sa.UUID(), nullable=False),
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("critical_gaps", JSONB(), nullable=False),
        sa.Column("minor_gaps", JSONB(), nullable=False),
        sa.Column("strengths", JSONB(), nullable=False),
        sa.Column("keyword_gaps", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_analysis_id"], ["job_analyses.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["master_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gap_analyses_job_analysis_id", "gap_analyses", ["job_analysis_id"])
    op.create_index("ix_gap_analyses_profile_id", "gap_analyses", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_gap_analyses_profile_id", table_name="gap_analyses")
    op.drop_index("ix_gap_analyses_job_analysis_id", table_name="gap_analyses")
    op.drop_table("gap_analyses")
