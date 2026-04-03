"""Add content_snapshot and section_overrides to generated_cvs

Revision ID: 0015
Revises: 0014
Create Date: 2026-04-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # content_snapshot: structured rendering context populated at generation time.
    # Nullable: pre-existing CVs have no snapshot; section editor gracefully handles NULL.
    op.add_column(
        "generated_cvs",
        sa.Column("content_snapshot", JSONB(), nullable=True),
    )
    # section_overrides: user edits keyed by section ID. Default is empty object.
    # Nullable at DB level; service layer treats NULL as {}.
    op.add_column(
        "generated_cvs",
        sa.Column("section_overrides", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_cvs", "section_overrides")
    op.drop_column("generated_cvs", "content_snapshot")
