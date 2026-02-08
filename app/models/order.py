from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.promo import PromoCode
    from app.models.address import Address

class Order(Base):
    __tablename__ = "order"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    order_number: Mapped[str] = mapped_column(String(8), unique=True, index=True)  # Unique 8-digit tracking ID
    status: Mapped[str] = mapped_column(String, default="pending", index=True)  # pending, paid, shipped, cancelled
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    shipping_address: Mapped[dict] = mapped_column(JSON) # Kept for backward compatibility, contains address snapshot
    shipping_address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("address.id"), nullable=True)
    billing_address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("address.id"), nullable=True)
    stripe_payment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(20), default="cod", index=True)  # cod, esewa, khalti, card
    promo_code_id: Mapped[Optional[int]] = mapped_column(ForeignKey("promocode.id"), nullable=True)
    discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    promo_code_rel: Mapped[Optional["PromoCode"]] = relationship("PromoCode", back_populates="orders")
    shipping_address_rel: Mapped[Optional["Address"]] = relationship("Address", foreign_keys=[shipping_address_id])

class OrderItem(Base):
    __tablename__ = "orderitem"

    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), index=True)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("productvariant.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant")
