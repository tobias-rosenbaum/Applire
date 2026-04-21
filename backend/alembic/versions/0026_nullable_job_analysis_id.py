"""Make interview_sessions.job_analysis_id nullable for Mode C

Revision ID: 0026
Revises: 0025
Create Date: 2026-04-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: Union[str, None] = "0025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "interview_sessions",
        "job_analysis_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "interview_sessions",
        "job_analysis_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
