"""add order payment_method column

Revision ID: e8f9a0b1c2d3
Revises: d7b6b5864eea
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, None] = 'd7b6b5864eea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('order', sa.Column('payment_method', sa.String(20), server_default='cod', nullable=False))
    op.create_index(op.f('ix_order_payment_method'), 'order', ['payment_method'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_order_payment_method'), table_name='order')
    op.drop_column('order', 'payment_method')
