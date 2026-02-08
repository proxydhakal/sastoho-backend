from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.token_service import token_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


def get_token_from_request(request: Request) -> str | None:
    """Get access token from HTTP-only cookie first, then Authorization header (for API clients)."""
    token = request.cookies.get(settings.COOKIE_ACCESS_TOKEN_NAME)
    if token:
        return token
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = get_token_from_request(request)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    
    # Check if token is blacklisted
    is_blacklisted = await token_service.is_token_blacklisted(db, token)
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Try to decode token
    payload = security.decode_token(token)
    if not payload:
        # Token might be expired, try to refresh
        raise credentials_exception
    
    token_type = payload.get("type")
    if token_type is not None and token_type != security.TOKEN_TYPE_ACCESS:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    try:
        u_id = int(user_id)
    except ValueError:
        raise credentials_exception
    user = await db.get(User, u_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    token = get_token_from_request(request)
    if not token:
        return None
    payload = security.decode_token(token)
    if not payload:
        return None
    token_type = payload.get("type")
    if token_type is not None and token_type != security.TOKEN_TYPE_ACCESS:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        u_id = int(user_id)
    except ValueError:
        return None
    user = await db.get(User, u_id)
    return user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user
