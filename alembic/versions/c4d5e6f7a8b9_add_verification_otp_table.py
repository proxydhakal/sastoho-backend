"""add verification_otp table for email OTP verification

Revision ID: c4d5e6f7a8b9
Revises: a7c8d9e0f1a2
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "a7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "verification_otp",
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("otp", sa.String(10), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_verification_otp_id"), "verification_otp", ["id"], unique=False)
    op.create_index(op.f("ix_verification_otp_email"), "verification_otp", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_verification_otp_email"), table_name="verification_otp")
    op.drop_index(op.f("ix_verification_otp_id"), table_name="verification_otp")
    op.drop_table("verification_otp")
