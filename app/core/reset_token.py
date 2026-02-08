from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.config import settings
from app.core.security import ALGORITHM

RESET_PASSWORD_EXPIRE_MINUTES = 60
VERIFY_EMAIL_EXPIRE_HOURS = 24


def create_password_reset_token(email: str) -> str:
    expires_delta = timedelta(minutes=RESET_PASSWORD_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": email, "type": "reset"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password_reset_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        email: str = payload.get("sub")
        return email
    except JWTError:
        return None


def create_verify_email_token(email: str) -> str:
    expires_delta = timedelta(hours=VERIFY_EMAIL_EXPIRE_HOURS)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": email, "type": "verify_email"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_email_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "verify_email":
            return None
        return payload.get("sub")
    except JWTError:
        return None
