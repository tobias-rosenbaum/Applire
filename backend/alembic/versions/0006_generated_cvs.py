"""Generated CVs table

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_cvs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_analysis_id", sa.UUID(), nullable=False),
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("tailored_data", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_analysis_id"], ["job_analyses.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["master_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_generated_cvs_job_analysis_id",
        "generated_cvs",
        ["job_analysis_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_generated_cvs_job_analysis_id", table_name="generated_cvs")
    op.drop_table("generated_cvs")
