"""flow_sessions: make job_id nullable

Allows creating a flow without a linked job (CV-only upload path).

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "flow_sessions",
        "job_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    # Back-fill any NULL job_ids before re-applying NOT NULL (manual step if needed)
    op.alter_column(
        "flow_sessions",
        "job_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
