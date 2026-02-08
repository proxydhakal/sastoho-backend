from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.v1.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.review import Review
from app.models.product import Product
from app.services.product_service import product_service
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter()

@router.post("/{product_slug}/reviews", response_model=ReviewOut)
async def create_review(
    product_slug: str,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a review for a product.
    """
    # Verify product exists
    product = await product_service.get_by_slug(db, slug=product_slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Optional: Verify purchase (Skipping as per plan, but good to note)
    
    review = Review(
        user_id=current_user.id,
        product_id=product.id,
        rating=review_in.rating,
        comment=review_in.comment,
        is_approved=True # Auto-approve for now
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    # Load relationships for response
    stmt = select(Review).filter(Review.id == review.id).options(
        selectinload(Review.user),
        selectinload(Review.product)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

@router.get("/{product_slug}/reviews", response_model=List[ReviewOut])
async def read_reviews(
    product_slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get reviews for a product.
    """
    product = await product_service.get_by_slug(db, slug=product_slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    stmt = select(Review).filter(
        Review.product_id == product.id, 
        Review.is_approved == True
    ).options(
        selectinload(Review.user),
        selectinload(Review.product)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
