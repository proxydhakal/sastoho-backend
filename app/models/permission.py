from typing import List, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user_group import UserGroup

class Permission(Base):
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    codename: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)  # e.g., "view_product", "edit_order"
    description: Mapped[str] = mapped_column(String, nullable=True)
    
    # Relationships
    groups: Mapped[List["UserGroup"]] = relationship(
        "UserGroup",
        secondary="group_permission_association",
        back_populates="permissions"
    )
