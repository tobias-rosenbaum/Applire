"""Add color_profiles, companies, user_settings tables; FK cols on generated_cvs and job_analyses

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "color_profiles",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("seed_primary", sa.String(7), nullable=False),
        sa.Column("derived", JSONB(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("color_profile_id", sa.UUID(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["color_profile_id"], ["color_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_table(
        "user_settings",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("default_color_profile_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["default_color_profile_id"], ["color_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("generated_cvs", sa.Column("color_profile_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_generated_cvs_color_profile",
        "generated_cvs", "color_profiles",
        ["color_profile_id"], ["id"],
    )
    op.add_column("job_analyses", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_job_analyses_company",
        "job_analyses", "companies",
        ["company_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_job_analyses_company", "job_analyses", type_="foreignkey")
    op.drop_column("job_analyses", "company_id")
    op.drop_constraint("fk_generated_cvs_color_profile", "generated_cvs", type_="foreignkey")
    op.drop_column("generated_cvs", "color_profile_id")
    op.drop_table("user_settings")
    op.drop_table("companies")
    op.drop_table("color_profiles")
