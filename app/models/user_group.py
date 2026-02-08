from typing import List, TYPE_CHECKING
from sqlalchemy import String, Table, Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.permission import Permission

# Association table for many-to-many relationship between User and UserGroup
user_group_association = Table(
    'user_group_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    Column('group_id', Integer, ForeignKey('usergroup.id', ondelete='CASCADE'), primary_key=True),
)

# Association table for many-to-many relationship between UserGroup and Permission
group_permission_association = Table(
    'group_permission_association',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('usergroup.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permission.id', ondelete='CASCADE'), primary_key=True),
)

class UserGroup(Base):
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_group_association,
        back_populates="groups"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=group_permission_association,
        back_populates="groups"
    )
