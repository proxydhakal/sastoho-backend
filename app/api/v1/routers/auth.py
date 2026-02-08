from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies.auth import get_current_user_optional, get_current_user
from app.core.database import get_db
from app.core import security
from app.core.config import settings
from app.core.reset_token import create_password_reset_token, verify_password_reset_token, create_verify_email_token, verify_email_token
from app.models.user import User
from app.schemas.user import Token, User as UserSchema, LoginResponse
from app.services.user_service import user_service
from app.services.token_service import token_service

router = APIRouter()

COOKIE_MAX_AGE_ACCESS = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
COOKIE_MAX_AGE_REFRESH = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.COOKIE_ACCESS_TOKEN_NAME,
        value=access_token,
        max_age=COOKIE_MAX_AGE_ACCESS,
        path=settings.COOKIE_PATH,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    response.set_cookie(
        key=settings.COOKIE_REFRESH_TOKEN_NAME,
        value=refresh_token,
        max_age=COOKIE_MAX_AGE_REFRESH,
        path=settings.COOKIE_PATH,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.COOKIE_ACCESS_TOKEN_NAME, path=settings.COOKIE_PATH)
    response.delete_cookie(settings.COOKIE_REFRESH_TOKEN_NAME, path=settings.COOKIE_PATH)


async def _user_to_schema(db, user_id: int) -> UserSchema | None:
    stmt = select(User).filter(User.id == user_id).options(selectinload(User.groups))
    result = await db.execute(stmt)
    user = result.scalars().first()
    return user


@router.post("/login", response_model=LoginResponse)
async def login_access_token(
    response: Response,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Login: sets HTTP-only cookies (access_token, refresh_token). Returns user. Use credentials: include and same-site origin.
    """
    user = await user_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Please verify your email before logging in. Check your inbox for the verification link.",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(subject=user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(subject=user.id)
    _set_auth_cookies(response, access_token, refresh_token)

    user_schema = await _user_to_schema(db, user.id)
    if not user_schema:
        raise HTTPException(status_code=500, detail="User not found after login")
    return LoginResponse(user=user_schema)


@router.post("/refresh", response_model=LoginResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token using refresh token from HTTP-only cookie. Sets new cookies. Call with credentials.
    """
    refresh_token = request.cookies.get(settings.COOKIE_REFRESH_TOKEN_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    # Check if refresh token is blacklisted
    is_blacklisted = await token_service.is_token_blacklisted(db, refresh_token)
    if is_blacklisted:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    
    user_id_str = security.verify_refresh_token(refresh_token)
    if not user_id_str:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    try:
        user_id = int(user_id_str)
    except ValueError:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access = security.create_access_token(subject=user_id, expires_delta=access_token_expires)
    new_refresh = security.create_refresh_token(subject=user_id)
    _set_auth_cookies(response, new_access, new_refresh)

    user_schema = await _user_to_schema(db, user_id)
    if not user_schema:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="User not found")
    return LoginResponse(user=user_schema)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional)
) -> Any:
    """
    Logout: Blacklist current tokens and clear auth cookies.
    """
    # Get tokens from cookies
    access_token = request.cookies.get(settings.COOKIE_ACCESS_TOKEN_NAME)
    refresh_token = request.cookies.get(settings.COOKIE_REFRESH_TOKEN_NAME)
    
    # Blacklist both tokens if they exist
    if access_token or refresh_token:
        await token_service.blacklist_tokens_from_request(
            db, 
            access_token, 
            refresh_token
        )
    
    # Clear cookies
    _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}
@router.post("/password-recovery/{email}", response_model=dict)
async def recover_password(email: str, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Password Recovery - sends reset link to email.
    """
    from app.core import email as email_utils
    from app.api.v1.routers.site_config import get_or_create_site_config

    user = await user_service.get_by_email(db, email=email)
    if not user:
        return {"msg": "If this email exists in the system, you will receive a reset link."}

    token = create_password_reset_token(email=email)
    site_config = await get_or_create_site_config(db)
    await email_utils.send_reset_password_email(
        email_to=user.email,
        token=token,
        full_name=user.full_name,
        logo_url=site_config.logo_url,
        site_title=site_config.site_title or "SastoHo",
    )
    return {"msg": "Password recovery email sent"}

@router.post("/verify-email", response_model=dict)
async def verify_email(
    token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify email address using token sent after signup.
    """
    email = verify_email_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user = await user_service.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"msg": "Email already verified. You can log in."}

    user.is_verified = True
    db.add(user)
    await db.commit()
    return {"msg": "Email verified successfully. You can now log in."}


@router.post("/reset-password/", response_model=dict)
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user = await user_service.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    hashed_password = security.get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    await db.commit()
    
    return {"msg": "Password updated successfully"}
