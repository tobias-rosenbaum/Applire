"""Rename color_profiles → cv_color_profiles, color_schemes → system_color_schemes

Revision ID: 0022
Revises: 0021
Create Date: 2026-04-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn: sa.engine.Connection, name: str) -> bool:
    return sa.inspect(conn).has_table(name)


def upgrade() -> None:
    conn = op.get_bind()
    # Only rename if the old table name exists — fresh installs create the tables
    # with the correct names directly in migrations 0020/0021, so this is a no-op there.
    if _table_exists(conn, "color_profiles"):
        op.rename_table("color_profiles", "cv_color_profiles")
    if _table_exists(conn, "color_schemes"):
        op.rename_table("color_schemes", "system_color_schemes")


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "system_color_schemes"):
        op.rename_table("system_color_schemes", "color_schemes")
    if _table_exists(conn, "cv_color_profiles"):
        op.rename_table("cv_color_profiles", "color_profiles")
