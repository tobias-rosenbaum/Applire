"""Add berufsbild_code and berufsbild_label to job_analyses (KldB 2020)

Revision ID: 0018
Revises: 0017
Create Date: 2026-04-07

Notes:
- Adds nullable VARCHAR(6) berufsbild_code (KldB 2020 classification code) and
  nullable TEXT berufsbild_label (German occupation name) to job_analyses.
- Source: Bundesagentur für Arbeit — Klassifikation der Berufe 2020 (BA-Klassifikation).
- Both columns are nullable: existing analyses and JDs where the LLM cannot confidently
  assign a code return NULL (not fatal).
- Runs on both PostgreSQL and SQLite (standard sa.String / sa.Text, no dialect-specific types).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "job_analyses",
        sa.Column("berufsbild_code", sa.String(6), nullable=True),
    )
    op.add_column(
        "job_analyses",
        sa.Column("berufsbild_label", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("job_analyses", "berufsbild_label")
    op.drop_column("job_analyses", "berufsbild_code")
