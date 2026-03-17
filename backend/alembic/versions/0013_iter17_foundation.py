"""Iteration 17 — Application Entity & API Hardening (foundation)

Creates `applications` table and hardens existing tables:
  - flow_sessions: + application_id (FK, nullable), + deleted_at
  - job_analyses:  + company_name (nullable)
  - generated_cvs: + status (TEXT, default 'ready'), + error_message (nullable)
  - uploads:       + user_id (FK → users, nullable — backfilled as NULL for
                     pre-existing rows; new rows set by profile router)

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. applications
    # ------------------------------------------------------------------
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("job_analysis_id", sa.UUID(), nullable=False),
        # workflow_status: system-managed, synced from FlowSession.current_step
        sa.Column(
            "workflow_status",
            sa.String(30),
            nullable=False,
            server_default="none",
        ),
        # user_status: user-managed via PATCH
        sa.Column(
            "user_status",
            sa.String(20),
            nullable=False,
            server_default="tracking",
        ),
        # Denormalized from JobAnalysis for fast list queries
        sa.Column("company_name", sa.Text(), nullable=True),
        sa.Column("role_title", sa.Text(), nullable=True),
        # User-managed fields
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        # 1:0..1 link to FlowSession — NULL until workflow is started
        sa.Column("flow_session_id", sa.UUID(), nullable=True),
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
        # GDPR TTL: inactivity timer, resets on every update (730 days)
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),  # overridden in service layer
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_analysis_id"], ["job_analyses.id"]),
        sa.ForeignKeyConstraint(["flow_session_id"], ["flow_sessions.id"]),
        # One application per (user, job) — enforced structurally
        sa.UniqueConstraint("user_id", "job_analysis_id", name="uq_application_user_job"),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_job_analysis_id", "applications", ["job_analysis_id"])

    # ------------------------------------------------------------------
    # 2. flow_sessions — add application_id and deleted_at
    # ------------------------------------------------------------------
    op.add_column(
        "flow_sessions",
        sa.Column("application_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "flow_sessions",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_flow_sessions_application_id",
        "flow_sessions",
        "applications",
        ["application_id"],
        ["id"],
    )

    # ------------------------------------------------------------------
    # 3. job_analyses — add company_name (LLM-extracted, best-effort)
    # ------------------------------------------------------------------
    op.add_column(
        "job_analyses",
        sa.Column("company_name", sa.Text(), nullable=True),
    )

    # ------------------------------------------------------------------
    # 4. generated_cvs — add async generation status + error_message
    #    Existing rows get status='ready' (they were synchronously generated).
    # ------------------------------------------------------------------
    op.add_column(
        "generated_cvs",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="ready",
        ),
    )
    op.add_column(
        "generated_cvs",
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    # ------------------------------------------------------------------
    # 5. uploads — add user_id for GDPR erasure scoping
    #    Nullable: pre-existing rows have no user association.
    # ------------------------------------------------------------------
    op.add_column(
        "uploads",
        sa.Column("user_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_uploads_user_id",
        "uploads",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_uploads_user_id", "uploads", type_="foreignkey")
    op.drop_column("uploads", "user_id")

    op.drop_column("generated_cvs", "error_message")
    op.drop_column("generated_cvs", "status")

    op.drop_column("job_analyses", "company_name")

    op.drop_constraint("fk_flow_sessions_application_id", "flow_sessions", type_="foreignkey")
    op.drop_column("flow_sessions", "deleted_at")
    op.drop_column("flow_sessions", "application_id")

    op.drop_index("ix_applications_job_analysis_id", table_name="applications")
    op.drop_index("ix_applications_user_id", table_name="applications")
    op.drop_table("applications")
