from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.wishlist import Wishlist
    from app.models.order import Order
    from app.models.review import Review
    from app.models.user_group import UserGroup
    from app.models.address import Address

class User(Base):
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    profile_image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="customer")

    # Relationships
    cart: Mapped["Cart"] = relationship("Cart", back_populates="user", uselist=False)
    wishlist: Mapped["Wishlist"] = relationship("Wishlist", back_populates="user", uselist=False)
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user")
    groups: Mapped[List["UserGroup"]] = relationship(
        "UserGroup",
        secondary="user_group_association",
        back_populates="users"
    )
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", cascade="all, delete-orphan")