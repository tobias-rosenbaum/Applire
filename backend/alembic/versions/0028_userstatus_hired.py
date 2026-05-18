"""add hired to UserStatus

Revision ID: 0028
Revises: 0027
Create Date: 2026-05-18

The Application.user_status column is stored as VARCHAR(20), not a Postgres
ENUM type, so this migration is a no-op at the database level. We keep the
no-op migration to keep the revision chain coherent and to document the
schema-level intent.
"""
from typing import Sequence, Union

from alembic import op  # noqa: F401

revision: str = "0028"
down_revision: Union[str, None] = "0027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: user_status is VARCHAR(20); valid values enforced at app level.
    pass


def downgrade() -> None:
    pass
