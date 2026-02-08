"""Add site config table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "siteconfig",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_title", sa.String(255), nullable=False, server_default="MEROSHOPPING"),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("meta_keywords", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(100), nullable=True),
        sa.Column("contact_address", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("favicon_url", sa.String(500), nullable=True),
        sa.Column("social_links", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_siteconfig_id"), "siteconfig", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_siteconfig_id"), table_name="siteconfig")
    op.drop_table("siteconfig")