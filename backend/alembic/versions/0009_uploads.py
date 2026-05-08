"""Uploads table for CV file storage (ADR 014)

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "uploads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("llm_tokens_used", sa.Integer(), nullable=True),
        sa.Column("llm_provider", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_uploads_expires_at", "uploads", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_uploads_expires_at", table_name="uploads")
    op.drop_table("uploads")
