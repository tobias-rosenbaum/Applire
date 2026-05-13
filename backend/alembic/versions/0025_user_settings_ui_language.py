"""Add ui_language to user_settings

Revision ID: 0025
Revises: 0024
Create Date: 2026-04-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: Union[str, None] = "0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("ui_language", sa.String(5), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "ui_language")
