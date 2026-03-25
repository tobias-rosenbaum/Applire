"""Create flow_sessions table — Iteration 15

Flow Orchestrator: tracks the end-to-end user journey from JD intake to CV download.
Parent context for interview_sessions (1:0..1 relationship).

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "flow_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        # Linear step enum: jd_analysis | cv_import | gap_analysis | interview | cv_generation | complete
        sa.Column(
            "current_step",
            sa.String(30),
            nullable=False,
            server_default="jd_analysis",
        ),
        # Resolved once at creation, immutable — drives available_actions routing
        sa.Column(
            "user_type",
            sa.String(20),
            nullable=False,
            server_default="new",
        ),
        # JSONB: {"next": "gap_analysis"} — varies per (step, user_type)
        sa.Column(
            "available_actions",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
        # Child artifact FKs — populated as flow progresses via advance_flow()
        sa.Column("gap_analysis_id", sa.UUID(), nullable=True),
        sa.Column("interview_session_id", sa.UUID(), nullable=True),
        sa.Column("generated_cv_id", sa.UUID(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["job_analyses.id"]),
        sa.ForeignKeyConstraint(["gap_analysis_id"], ["gap_analyses.id"]),
        sa.ForeignKeyConstraint(["interview_session_id"], ["interview_sessions.id"]),
        sa.ForeignKeyConstraint(["generated_cv_id"], ["generated_cvs.id"]),
        # One flow per (user_id, job_id) — idempotent creation
        sa.UniqueConstraint("user_id", "job_id", name="uq_flow_session_user_job"),
    )
    op.create_index("ix_flow_sessions_user_id", "flow_sessions", ["user_id"])
    op.create_index("ix_flow_sessions_job_id", "flow_sessions", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_flow_sessions_job_id", table_name="flow_sessions")
    op.drop_index("ix_flow_sessions_user_id", table_name="flow_sessions")
    op.drop_table("flow_sessions")
