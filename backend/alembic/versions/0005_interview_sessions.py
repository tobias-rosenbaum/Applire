"""Interview sessions table

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_analysis_id", sa.UUID(), nullable=False),
        sa.Column("gap_analysis_id", sa.UUID(), nullable=False),
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("state", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_analysis_id"], ["job_analyses.id"]),
        sa.ForeignKeyConstraint(["gap_analysis_id"], ["gap_analyses.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["master_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interview_sessions_job_analysis_id",
        "interview_sessions",
        ["job_analysis_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_interview_sessions_job_analysis_id", table_name="interview_sessions"
    )
    op.drop_table("interview_sessions")
