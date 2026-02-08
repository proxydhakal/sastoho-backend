from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, DECIMAL, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order


class PromoCode(Base):
    __tablename__ = "promocode"
    
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    discount_type: Mapped[str] = mapped_column(String(20), default="percentage")  # "percentage" or "fixed"
    discount_value: Mapped[float] = mapped_column(DECIMAL(10, 2))  # Percentage (0-100) or fixed amount
    min_purchase_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    max_discount_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Total usage limit
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="promo_code_rel")


class PromoCodeUsage(Base):
    __tablename__ = "promocodeusage"
    
    promo_code_id: Mapped[int] = mapped_column(ForeignKey("promocode.id"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"))
    discount_amount: Mapped[float] = mapped_column(DECIMAL(10, 2))
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    promo_code: Mapped["PromoCode"] = relationship("PromoCode")
    user: Mapped[Optional["User"]] = relationship("User")
    order: Mapped["Order"] = relationship("Order")
