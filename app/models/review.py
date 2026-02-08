from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Review(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer) # 1-5
    comment: Mapped[str] = mapped_column(String, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True) # Simple moderation
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
