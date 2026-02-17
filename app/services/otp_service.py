"""OTP storage and verification using the database (works without Redis)."""
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification_otp import VerificationOtp


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


async def set_otp_db(
    db: AsyncSession,
    email: str,
    otp: str,
    expire_seconds: int = 600,
) -> None:
    """Store OTP for email. Replaces any existing OTP for that email."""
    key_email = _normalize_email(email)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
    # Remove any existing OTP for this email
    await db.execute(delete(VerificationOtp).where(VerificationOtp.email == key_email))
    db.add(VerificationOtp(email=key_email, otp=otp, expires_at=expires_at))
    await db.commit()


async def get_and_delete_otp_db(db: AsyncSession, email: str) -> Optional[str]:
    """Get OTP for email and delete it (one-time use). Returns None if invalid or expired."""
    key_email = _normalize_email(email)
    result = await db.execute(
        select(VerificationOtp)
        .where(VerificationOtp.email == key_email)
        .where(VerificationOtp.expires_at > datetime.now(timezone.utc))
        .limit(1)
    )
    row = result.scalars().first()
    if not row:
        return None
    otp = row.otp
    await db.delete(row)
    await db.commit()
    return otp
