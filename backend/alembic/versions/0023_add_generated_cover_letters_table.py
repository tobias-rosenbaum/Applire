"""Add generated_cover_letters table

Revision ID: 0023
Revises: 0022
Create Date: 2026-04-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_cover_letters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_analysis_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("template", sa.String(40), nullable=False, server_default="classic_german"),
        sa.Column("letter_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("pre_gen_inputs", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("section_overrides", sa.JSON(), nullable=True),
        sa.Column("color_profile_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["color_profile_id"], ["cv_color_profiles.id"]),
        sa.ForeignKeyConstraint(["job_analysis_id"], ["job_analyses.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["master_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_generated_cover_letters_job_analysis_id",
        "generated_cover_letters",
        ["job_analysis_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_generated_cover_letters_job_analysis_id",
        table_name="generated_cover_letters",
    )
    op.drop_table("generated_cover_letters")
