"""Add template column to generated_cvs

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "generated_cvs",
        sa.Column(
            "template",
            sa.String(length=32),
            nullable=False,
            server_default="classic_german",
        ),
    )


def downgrade() -> None:
    op.drop_column("generated_cvs", "template")
