"""Add generated_cover_letter_id FK to flow_sessions

Revision ID: 0024
Revises: 0023
Create Date: 2026-04-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "flow_sessions",
        sa.Column("generated_cover_letter_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_flow_sessions_cover_letter",
        "flow_sessions",
        "generated_cover_letters",
        ["generated_cover_letter_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_flow_sessions_cover_letter", "flow_sessions", type_="foreignkey"
    )
    op.drop_column("flow_sessions", "generated_cover_letter_id")
