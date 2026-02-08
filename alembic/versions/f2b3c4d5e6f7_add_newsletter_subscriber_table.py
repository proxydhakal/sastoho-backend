"""add newsletter_subscriber table

Revision ID: f2b3c4d5e6f7
Revises: e8f9a0b1c2d3
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2b3c4d5e6f7'
down_revision: Union[str, None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('newsletter_subscriber',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_newsletter_subscriber_email'), 'newsletter_subscriber', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_newsletter_subscriber_email'), table_name='newsletter_subscriber')
    op.drop_table('newsletter_subscriber')
