"""add order_number to order table

Revision ID: a7c8d9e0f1a2
Revises: f2b3c4d5e6f7
Create Date: 2026-02-06

"""
import random
import string
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy import inspect as sa_inspect

revision: str = "a7c8d9e0f1a2"
down_revision: Union[str, None] = "f2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORDER_NUMBER_CHARS = string.ascii_uppercase + string.digits
ORDER_NUMBER_LENGTH = 8


def _random_order_number() -> str:
    return "".join(random.choices(ORDER_NUMBER_CHARS, k=ORDER_NUMBER_LENGTH))


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("order")]
    if "order_number" not in columns:
        op.add_column("order", sa.Column("order_number", sa.String(8), nullable=True))
    # Backfill existing orders: unique 8-char alphanumeric per row
    order_table = "`order`" if conn.dialect.name == "mysql" else '"order"'
    result = conn.execute(text(f"SELECT id FROM {order_table} WHERE order_number IS NULL"))
    rows = result.fetchall()
    used = set()
    for (order_id,) in rows:
        while True:
            code = _random_order_number()
            if code not in used:
                used.add(code)
                break
        conn.execute(text(f"UPDATE {order_table} SET order_number = :code WHERE id = :id"), {"code": code, "id": order_id})
    op.alter_column(
        "order",
        "order_number",
        nullable=False,
        existing_type=sa.String(8),
    )
    index_names = [idx["name"] for idx in inspector.get_indexes("order")]
    if op.f("ix_order_order_number") not in index_names:
        op.create_index(op.f("ix_order_order_number"), "order", ["order_number"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_order_order_number"), table_name="order")
    op.drop_column("order", "order_number")
