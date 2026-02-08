from typing import List, Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import Base

class Cart(Base):
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="cart") # One-to-One mostly, or One-to-Many if history kept (but usually current cart)
    items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan", lazy="selectin")

class CartItem(Base):
    cart_id: Mapped[int] = mapped_column(ForeignKey("cart.id"))
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("productvariant.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant", lazy="selectin") # Eager load variant details
