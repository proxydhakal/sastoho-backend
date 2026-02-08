from typing import List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import Base

class Wishlist(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wishlist")
    items: Mapped[List["WishlistItem"]] = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan", lazy="selectin")

class WishlistItem(Base):
    wishlist_id: Mapped[int] = mapped_column(ForeignKey("wishlist.id"))
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("productvariant.id"))
    
    # Relationships
    wishlist: Mapped["Wishlist"] = relationship("Wishlist", back_populates="items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant", lazy="selectin")
