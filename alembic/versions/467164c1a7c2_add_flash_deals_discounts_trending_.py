"""add_flash_deals_discounts_trending_promo_codes

Revision ID: 467164c1a7c2
Revises: b2c3d4e5f6a7
Create Date: 2026-02-06 15:25:55.579033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '467164c1a7c2'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, name: str) -> bool:
    return name in inspect(conn).get_table_names()


def _column_exists(conn, table: str, column: str) -> bool:
    if not _table_exists(conn, table):
        return False
    cols = [c['name'] for c in inspect(conn).get_columns(table)]
    return column in cols


def upgrade() -> None:
    conn = op.get_bind()

    # Skip create_table if tables already exist (e.g. after partial failed run)
    if not _table_exists(conn, 'promocode'):
        op.create_table('promocode',
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('description', sa.String(length=500), nullable=True),
            sa.Column('discount_type', sa.String(length=20), nullable=False),
            sa.Column('discount_value', sa.DECIMAL(precision=10, scale=2), nullable=False),
            sa.Column('min_purchase_amount', sa.DECIMAL(precision=10, scale=2), nullable=True),
            sa.Column('max_discount_amount', sa.DECIMAL(precision=10, scale=2), nullable=True),
            sa.Column('usage_limit', sa.Integer(), nullable=True),
            sa.Column('used_count', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
            sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_promocode_code'), 'promocode', ['code'], unique=True)
        op.create_index(op.f('ix_promocode_id'), 'promocode', ['id'], unique=False)
    if not _table_exists(conn, 'promocodeusage'):
        op.create_table('promocodeusage',
            sa.Column('promo_code_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('discount_amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
            sa.Column('used_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
            sa.ForeignKeyConstraint(['promo_code_id'], ['promocode.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_promocodeusage_id'), 'promocodeusage', ['id'], unique=False)
    if not _column_exists(conn, 'order', 'promo_code_id'):
        op.add_column('order', sa.Column('promo_code_id', sa.Integer(), nullable=True))
    if not _column_exists(conn, 'order', 'discount_amount'):
        op.add_column('order', sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=True))
    try:
        op.create_foreign_key(None, 'order', 'promocode', ['promo_code_id'], ['id'])
    except Exception:
        pass  # FK may already exist after partial run

    # Add product columns if missing (MySQL: Boolean default 0/1)
    if not _column_exists(conn, 'product', 'is_flash_deal'):
        op.add_column('product', sa.Column('is_flash_deal', sa.Boolean(), nullable=True, server_default=sa.text('0')))
        op.add_column('product', sa.Column('flash_deal_start', sa.DateTime(timezone=True), nullable=True))
        op.add_column('product', sa.Column('flash_deal_end', sa.DateTime(timezone=True), nullable=True))
        op.add_column('product', sa.Column('flash_deal_price', sa.DECIMAL(precision=10, scale=2), nullable=True))
        op.add_column('product', sa.Column('discount_percentage', sa.DECIMAL(precision=5, scale=2), nullable=True))
        op.add_column('product', sa.Column('discount_amount', sa.DECIMAL(precision=10, scale=2), nullable=True))
        op.add_column('product', sa.Column('is_trending', sa.Boolean(), nullable=True, server_default=sa.text('0')))
        op.add_column('product', sa.Column('view_count', sa.Integer(), nullable=True, server_default=sa.text('0')))
        op.execute("UPDATE product SET is_flash_deal = 0 WHERE is_flash_deal IS NULL")
        op.execute("UPDATE product SET is_trending = 0 WHERE is_trending IS NULL")
        op.execute("UPDATE product SET view_count = 0 WHERE view_count IS NULL")
        # MySQL requires existing_type when altering columns
        op.alter_column('product', 'is_flash_deal', existing_type=sa.Boolean(), nullable=False)
        op.alter_column('product', 'is_trending', existing_type=sa.Boolean(), nullable=False)
        op.alter_column('product', 'view_count', existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product', 'view_count')
    op.drop_column('product', 'is_trending')
    op.drop_column('product', 'discount_amount')
    op.drop_column('product', 'discount_percentage')
    op.drop_column('product', 'flash_deal_price')
    op.drop_column('product', 'flash_deal_end')
    op.drop_column('product', 'flash_deal_start')
    op.drop_column('product', 'is_flash_deal')
    op.drop_constraint(None, 'order', type_='foreignkey')
    op.drop_column('order', 'discount_amount')
    op.drop_column('order', 'promo_code_id')
    op.drop_index(op.f('ix_promocodeusage_id'), table_name='promocodeusage')
    op.drop_table('promocodeusage')
    op.drop_index(op.f('ix_promocode_id'), table_name='promocode')
    op.drop_index(op.f('ix_promocode_code'), table_name='promocode')
    op.drop_table('promocode')
    # ### end Alembic commands ###
