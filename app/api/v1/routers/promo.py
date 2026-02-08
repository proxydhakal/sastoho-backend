from typing import List, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from decimal import Decimal

from app.api.v1.dependencies.auth import get_current_admin_user, get_current_user
from app.core.database import get_db
from app.schemas.promo import PromoCode, PromoCodeCreate, PromoCodeUpdate, PromoCodeValidate, PromoCodeValidationResult
from app.services.promo_service import promo_code_service
from app.models.user import User
from app.models.promo import PromoCode as PromoCodeModel

router = APIRouter()


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware UTC for DB storage."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.get("/promo-codes", response_model=List[PromoCode])
async def read_promo_codes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """Get all promo codes (admin only). Optional search by code or description."""
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = select(PromoCodeModel).where(
            or_(
                PromoCodeModel.code.ilike(term),
                PromoCodeModel.description.ilike(term),
            )
        ).offset(skip).limit(limit)
        result = await db.execute(stmt)
        promo_codes = result.scalars().all()
    else:
        promo_codes = await promo_code_service.get_multi(db, skip=skip, limit=limit)
    return promo_codes


@router.post("/promo-codes", response_model=PromoCode)
async def create_promo_code(
    promo_code_in: PromoCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """Create a new promo code (admin only)."""
    code = promo_code_in.code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Promo code is required")
    db_obj = PromoCodeModel(
        code=code,
        description=promo_code_in.description,
        discount_type=promo_code_in.discount_type,
        discount_value=promo_code_in.discount_value,
        min_purchase_amount=promo_code_in.min_purchase_amount,
        max_discount_amount=promo_code_in.max_discount_amount,
        usage_limit=promo_code_in.usage_limit,
        is_active=promo_code_in.is_active,
        valid_from=_ensure_utc(promo_code_in.valid_from),
        valid_until=_ensure_utc(promo_code_in.valid_until),
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.patch("/promo-codes/{promo_code_id}", response_model=PromoCode)
async def update_promo_code(
    promo_code_id: int,
    promo_code_in: PromoCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """Update a promo code (admin only)."""
    promo_code = await promo_code_service.get(db, id=promo_code_id)
    if not promo_code:
        raise HTTPException(status_code=404, detail="Promo code not found")
    if promo_code_in.code:
        promo_code_in.code = promo_code_in.code.upper()
    promo_code = await promo_code_service.update(db, db_obj=promo_code, obj_in=promo_code_in)
    return promo_code


@router.delete("/promo-codes/{promo_code_id}", response_model=dict)
async def delete_promo_code(
    promo_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """Delete a promo code (admin only)."""
    promo_code = await promo_code_service.get(db, id=promo_code_id)
    if not promo_code:
        raise HTTPException(status_code=404, detail="Promo code not found")
    await promo_code_service.remove(db, id=promo_code_id)
    return {"msg": "Promo code deleted successfully"}


@router.post("/promo-codes/validate", response_model=PromoCodeValidationResult)
async def validate_promo_code(
    validation_data: PromoCodeValidate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Validate a promo code and get discount amount."""
    result = await promo_code_service.validate_promo_code(
        db,
        code=validation_data.code,
        total_amount=validation_data.total_amount,
        user_id=current_user.id if current_user else None
    )
    return result
