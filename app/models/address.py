from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import foreign
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order

class Address(Base):
    __tablename__ = "address"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    street: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=True)
    postal_code: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=False, default="Nepal")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    address_type: Mapped[str] = mapped_column(String, default="shipping")  # shipping or billing

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    # Note: orders relationship removed to avoid ambiguity with multiple foreign keys
    # Use shipping_address_rel on Order model instead
