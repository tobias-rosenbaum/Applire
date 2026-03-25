"""Add source_url to job_analyses

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "job_analyses",
        sa.Column("source_url", sa.Text(), nullable=True),
    )
    op.create_index("ix_job_analyses_source_url", "job_analyses", ["source_url"])


def downgrade() -> None:
    op.drop_index("ix_job_analyses_source_url", table_name="job_analyses")
    op.drop_column("job_analyses", "source_url")
