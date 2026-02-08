"""Add user groups and permissions

Revision ID: f1a2b3c4d5e6
Revises: 2ab96d00f2f8
Create Date: 2026-02-05 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '2ab96d00f2f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Permission table
    op.create_table(
        'permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('codename', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permission_id'), 'permission', ['id'], unique=False)
    op.create_index(op.f('ix_permission_name'), 'permission', ['name'], unique=True)
    op.create_index(op.f('ix_permission_codename'), 'permission', ['codename'], unique=True)

    # Create UserGroup table
    op.create_table(
        'usergroup',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usergroup_id'), 'usergroup', ['id'], unique=False)
    op.create_index(op.f('ix_usergroup_name'), 'usergroup', ['name'], unique=True)

    # Create association tables
    op.create_table(
        'user_group_association',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['usergroup.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'group_id')
    )

    op.create_table(
        'group_permission_association',
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['usergroup.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('group_id', 'permission_id')
    )

    # Insert default permissions
    op.execute("""
        INSERT INTO permission (name, codename, description) VALUES
        ('View Products', 'view_product', 'Can view products'),
        ('Add Products', 'add_product', 'Can add new products'),
        ('Change Products', 'change_product', 'Can modify existing products'),
        ('Delete Products', 'delete_product', 'Can delete products'),
        ('View Orders', 'view_order', 'Can view orders'),
        ('Change Orders', 'change_order', 'Can modify orders'),
        ('View Users', 'view_user', 'Can view users'),
        ('Add Users', 'add_user', 'Can add new users'),
        ('Change Users', 'change_user', 'Can modify users'),
        ('Delete Users', 'delete_user', 'Can delete users'),
        ('View Categories', 'view_category', 'Can view categories'),
        ('Add Categories', 'add_category', 'Can add categories'),
        ('Change Categories', 'change_category', 'Can modify categories'),
        ('Delete Categories', 'delete_category', 'Can delete categories')
    """)


def downgrade() -> None:
    op.drop_table('group_permission_association')
    op.drop_table('user_group_association')
    op.drop_index(op.f('ix_usergroup_name'), table_name='usergroup')
    op.drop_index(op.f('ix_usergroup_id'), table_name='usergroup')
    op.drop_table('usergroup')
    op.drop_index(op.f('ix_permission_codename'), table_name='permission')
    op.drop_index(op.f('ix_permission_name'), table_name='permission')
    op.drop_index(op.f('ix_permission_id'), table_name='permission')
    op.drop_table('permission')
