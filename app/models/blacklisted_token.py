from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class BlacklistedToken(Base):
    """
    Store blacklisted JWT tokens to prevent their use after logout.
    Tokens are stored by their jti (JWT ID) or the full token string.
    """
    __tablename__ = "blacklisted_token"
    
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'access' or 'refresh'
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    blacklisted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_token_type', 'token', 'token_type'),
    )
