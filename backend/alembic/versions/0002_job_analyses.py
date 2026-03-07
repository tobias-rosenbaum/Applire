"""Job analyses table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_analyses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("raw_text_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("role_title", sa.Text(), nullable=False),
        sa.Column("required_skills", JSONB(), nullable=False),
        sa.Column("nice_to_have_skills", JSONB(), nullable=False),
        sa.Column("keywords", JSONB(), nullable=False),
        sa.Column("seniority_level", sa.Text(), nullable=False),
        sa.Column("company_culture_signals", JSONB(), nullable=False),
        sa.Column("language_requirement", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_text_hash"),
    )


def downgrade() -> None:
    op.drop_table("job_analyses")
