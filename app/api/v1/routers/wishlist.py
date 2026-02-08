from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.wishlist import Wishlist
from app.services.wishlist_service import wishlist_service

router = APIRouter()

@router.get("/", response_model=Wishlist)
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get user's wishlist.
    """
    wishlist = await wishlist_service.get_wishlist(db, user_id=current_user.id)
    return wishlist

@router.post("/items", response_model=Wishlist)
async def add_wishlist_item(
    variant_id: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add item to wishlist.
    """
    wishlist = await wishlist_service.add_item(db, user_id=current_user.id, variant_id=variant_id)
    return wishlist

@router.delete("/items/{variant_id}", response_model=Wishlist)
async def remove_wishlist_item(
    variant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Remove item from wishlist.
    """
    wishlist = await wishlist_service.remove_item(db, user_id=current_user.id, variant_id=variant_id)
    return wishlist
