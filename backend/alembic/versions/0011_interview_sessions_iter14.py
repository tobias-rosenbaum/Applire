"""Interview sessions — Iteration 14 columns and constraints

Adds: mode, questions_asked, hard_ceiling, expires_at
Fixes: gap_analysis_id → nullable (MODE B sessions start without a gap analysis)
Adds: partial unique index uq_active_session_per_job

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make gap_analysis_id nullable (MODE B sessions have no gap analysis at creation)
    op.alter_column("interview_sessions", "gap_analysis_id", nullable=True)

    # Add new columns
    op.add_column(
        "interview_sessions",
        sa.Column(
            "mode",
            sa.String(20),
            nullable=False,
            server_default="targeted",
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "questions_asked",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "hard_ceiling",
            sa.Integer(),
            nullable=False,
            server_default="12",
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Partial unique index: one active session per (user_id, job_analysis_id).
    # user_id is not yet a column — sessions are single-user in Community Edition.
    # The constraint is on job_analysis_id alone for now; Cloud Edition will add
    # a user_id column and update this index via a Cloud-only migration.
    op.create_index(
        "uq_active_session_per_job",
        "interview_sessions",
        ["job_analysis_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_session_per_job", table_name="interview_sessions")
    op.drop_column("interview_sessions", "expires_at")
    op.drop_column("interview_sessions", "hard_ceiling")
    op.drop_column("interview_sessions", "questions_asked")
    op.drop_column("interview_sessions", "mode")
    op.alter_column("interview_sessions", "gap_analysis_id", nullable=False)
