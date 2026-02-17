"""OTP storage for email verification. Uses Redis with in-memory fallback when Redis is unavailable."""
import random
import string
import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings

OTP_EXPIRE_SECONDS = 600  # 10 minutes
OTP_KEY_PREFIX = "verify_otp:"
_redis_client = None
_in_memory_store: dict[str, tuple[str, float]] = {}
_in_memory_lock = asyncio.Lock()


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as redis
            _redis_client = redis.from_url(settings.REDIS_URL)
        except Exception:
            _redis_client = False  # Mark as failed
    return _redis_client if _redis_client else None


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


def _normalize_email(email: str) -> str:
    """Normalize email for storage/lookup so casing and whitespace don't break verification."""
    return (email or "").strip().lower()


async def set_otp(email: str, otp: str, expire_seconds: int = OTP_EXPIRE_SECONDS) -> None:
    """Store OTP for email with expiry."""
    key_email = _normalize_email(email)
    redis = _get_redis()
    if redis:
        try:
            key = f"{OTP_KEY_PREFIX}{key_email}"
            await redis.setex(key, expire_seconds, otp)
            return
        except Exception:
            pass
    # Fallback: in-memory (single process only)
    async with _in_memory_lock:
        _in_memory_store[key_email] = (otp, datetime.now(timezone.utc).timestamp() + expire_seconds)


async def get_and_delete_otp(email: str) -> Optional[str]:
    """Get OTP for email and delete it (one-time use). Returns None if invalid or expired."""
    key_email = _normalize_email(email)
    redis = _get_redis()
    if redis:
        try:
            key = f"{OTP_KEY_PREFIX}{key_email}"
            otp = await redis.get(key)
            if otp:
                await redis.delete(key)
                return otp.decode() if isinstance(otp, bytes) else str(otp)
            return None
        except Exception:
            return None
    # Fallback: in-memory
    async with _in_memory_lock:
        entry = _in_memory_store.pop(key_email, None)
        if not entry:
            return None
        otp, expiry = entry
        if datetime.now(timezone.utc).timestamp() > expiry:
            return None
        return otp
