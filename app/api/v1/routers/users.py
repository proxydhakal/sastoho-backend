from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import os
import uuid
from pathlib import Path

from app.api.v1.dependencies.auth import get_current_active_user
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserPasswordUpdate, User as UserSchema, UserUpdate
from app.services.user_service import user_service

router = APIRouter()

@router.post("/", response_model=dict)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user. Sends verification email; user must verify before logging in.
    """
    from app.core import email as email_utils
    from app.core.reset_token import create_verify_email_token
    from app.api.v1.routers.site_config import get_or_create_site_config

    user = await user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await user_service.create_user(db, user_in=user_in)
    token = create_verify_email_token(email=user.email)
    site_config = await get_or_create_site_config(db)
    await email_utils.send_verification_email(
        email_to=user.email,
        token=token,
        full_name=user.full_name,
        logo_url=site_config.logo_url,
        site_title=site_config.site_title or "SastoHo",
    )
    return {
        "msg": "Account created. Please check your email to verify your account before logging in.",
        "email": user.email,
    }

@router.get("/me", response_model=UserSchema)
async def read_user_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    # Eagerly load groups to avoid lazy loading issues
    stmt = select(User).filter(User.id == current_user.id).options(selectinload(User.groups))
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.patch("/me", response_model=UserSchema)
async def update_user_me(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user profile.
    """
    update_data = user_update.model_dump(exclude_unset=True, exclude={"password", "group_ids"})
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    # Reload with groups
    stmt = select(User).filter(User.id == current_user.id).options(selectinload(User.groups))
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    return user

@router.post("/me/profile-image", response_model=UserSchema)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Upload profile image for current user.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.")
    
    # Validate file size (max 5MB)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit.")
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR) / "profiles"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Delete old profile image if exists
    if current_user.profile_image:
        old_path = Path(settings.UPLOAD_DIR) / current_user.profile_image.lstrip("/")
        if old_path.exists():
            old_path.unlink()
    
    # Update user profile_image
    current_user.profile_image = f"/uploads/profiles/{unique_filename}"
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    # Reload with groups
    stmt = select(User).filter(User.id == current_user.id).options(selectinload(User.groups))
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    return user

@router.patch("/me/password", response_model=Any)
async def update_password(
    password_update: UserPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user password.
    """
    from app.core.security import verify_password, get_password_hash
    
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    hashed_password = get_password_hash(password_update.new_password)
    current_user.hashed_password = hashed_password
    db.add(current_user)
    await db.commit()
    
    return {"msg": "Password updated successfully"}
