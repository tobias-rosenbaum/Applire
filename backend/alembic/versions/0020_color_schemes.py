"""Add color_schemes table

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-10
"""
from typing import Sequence, Union
import json
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EU_BLUE_ID = "a0000000-0000-0000-0000-000000000001"

_EU_BLUE_DERIVED = {
    "--color-primary": "#1b4f72",
    "--color-primary-container": "#dee7ed",
    "--color-teal": "#2a8f9d",
    "--color-teal-dim": "#00363d",
    "--color-teal-container": "#e2f1f3",
    "--color-teal-container-light": "#f6f8f8",
    "--color-gold": "#c9a84c",
    "--color-gold-dim": "#664b00",
    "--color-gold-container": "#f7f0de",
    "--color-surface-dim": "#e4eaee",
    "--color-surface-bright": "#ffffff",
    "--color-surface-container": "#dde5ea",
    "--color-surface-container-high": "#d6dfe6",
    "--color-surface-container-highest": "#d1dce3",
    "--color-neutral-light": "#e8edf1",
}


def upgrade() -> None:
    op.create_table(
        "color_schemes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("seed_primary", sa.String(7), nullable=False),
        sa.Column("seed_accent", sa.String(7), nullable=False),
        sa.Column("seed_secondary", sa.String(7), nullable=False),
        sa.Column("surface_lightness", sa.Float(), nullable=False, server_default="0.97"),
        sa.Column("derived", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Seed EU Blue as the single built-in active scheme
    op.execute(
        sa.text(
            "INSERT INTO color_schemes "
            "(id, name, is_active, is_builtin, seed_primary, seed_accent, seed_secondary, "
            "surface_lightness, derived, created_at) VALUES "
            "(CAST(:id AS UUID), :name, true, true, :sp, :sa, :ss, :sl, CAST(:derived AS JSONB), CAST(:created_at AS TIMESTAMPTZ))"
        ).bindparams(
            id=_EU_BLUE_ID,
            name="EU Blue",
            sp="#1B4F72",
            sa="#2A8F9D",
            ss="#C9A84C",
            sl=0.80,
            derived=json.dumps(_EU_BLUE_DERIVED),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )


def downgrade() -> None:
    op.drop_table("color_schemes")
