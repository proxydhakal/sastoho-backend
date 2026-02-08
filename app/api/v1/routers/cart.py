from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies.auth import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.cart import Cart, CartItem
from app.services.cart_service import cart_service

router = APIRouter()

async def get_or_create_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Get session_id from header or generate a new one for guest users."""
    if x_session_id:
        return x_session_id
    # Generate a new session ID if not provided
    import uuid
    return f"guest_{uuid.uuid4().hex}"

@router.get("/", response_model=Cart)
async def get_cart(
    current_user: Optional[User] = Depends(get_current_user_optional),
    session_id: str = Depends(get_or_create_session_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current cart. Depends on user auth or X-Session-ID header.
    Returns empty cart structure if no cart exists.
    Automatically creates session_id for guest users if not provided.
    """
    user_id = current_user.id if current_user else None
    
    # If authenticated, use user_id; otherwise use session_id
    cart = await cart_service.get_cart(db, user_id=user_id, session_id=session_id if not user_id else None)
    if not cart:
        # Return empty cart structure instead of 404
        return Cart(id=0, items=[], user_id=user_id, session_id=session_id if not user_id else None)
    return cart

@router.post("/items", response_model=Cart)
async def add_cart_item(
    variant_id: int = Body(..., embed=True),
    quantity: int = Body(..., embed=True),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session_id: str = Depends(get_or_create_session_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add item to cart. Creates cart if missing.
    Automatically creates session_id for guest users if not provided.
    """
    user_id = current_user.id if current_user else None
    
    cart = await cart_service.add_item(db, variant_id=variant_id, quantity=quantity, user_id=user_id, session_id=session_id if not user_id else None)
    return cart

@router.patch("/items/{item_id}", response_model=Cart)
async def update_cart_item(
    item_id: int,
    quantity: int = Body(..., embed=True),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session_id: str = Depends(get_or_create_session_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update item quantity.
    """
    user_id = current_user.id if current_user else None
    cart = await cart_service.update_item_quantity(db, item_id=item_id, quantity=quantity, user_id=user_id, session_id=session_id if not user_id else None)
    if not cart:
         raise HTTPException(status_code=404, detail="Cart or item not found")
    return cart

@router.delete("/items/{item_id}", response_model=Cart)
async def remove_cart_item(
    item_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    session_id: str = Depends(get_or_create_session_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Remove item from cart.
    """
    user_id = current_user.id if current_user else None
    cart = await cart_service.remove_item(db, item_id=item_id, user_id=user_id, session_id=session_id if not user_id else None)
    if not cart:
         raise HTTPException(status_code=404, detail="Cart or item not found")
    return cart

@router.post("/merge", response_model=Cart)
async def merge_cart(
    session_id: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Merge guest cart (session_id) into authenticated user's cart.
    """
    cart = await cart_service.merge_carts(db, session_id=session_id, user_id=current_user.id)
    return cart
