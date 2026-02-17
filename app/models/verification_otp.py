"""Email verification OTP stored in DB (works without Redis, survives restarts)."""
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class VerificationOtp(Base):
    """One-time verification code for email verification. Deleted after use or expiry."""

    __tablename__ = "verification_otp"

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    otp: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
