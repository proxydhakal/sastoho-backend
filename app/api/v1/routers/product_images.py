from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies.auth import get_current_admin_user
from app.core.database import get_db
from app.core.storage import save_product_image, delete_product_image
from app.models.product import Product, ProductVariant, ProductImage
from app.schemas.product import ProductImage as ProductImageSchema
from app.services.product_service import product_service
from app.models.user import User
from app.services.product_service import product_service

router = APIRouter()


@router.post("/products/{slug}/images", response_model=List[ProductImageSchema])
async def upload_product_images(
    slug: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> List[ProductImageSchema]:
    """
    Upload multiple images for a product.
    Max 1MB per image, only JPG, JPEG, PNG allowed.
    """
    # Verify product exists
    product = await product_service.get_by_slug(db, slug=slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_id = product.id
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one image file is required")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed per upload")
    
    saved_images = []
    
    for idx, file in enumerate(files):
        try:
            # Save image file
            relative_path = await save_product_image(file, product_id)
            # Store relative path (without leading slash) so frontend can construct full URL
            # Frontend will prepend API_URL if needed
            image_url = relative_path.replace('\\', '/')
            
            # Create ProductImage record
            product_image = ProductImage(
                product_id=product_id,
                variant_id=None,
                url=image_url,
                is_main=(idx == 0)  # First image is main by default
            )
            db.add(product_image)
            saved_images.append(product_image)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error uploading {file.filename}: {str(e)}")
    
    await db.commit()
    
    # Refresh images to return with IDs and ensure they're linked
    for img in saved_images:
        await db.refresh(img)
        # Verify the image was saved correctly
        print(f"Saved image {img.id}: product_id={img.product_id}, variant_id={img.variant_id}, url={img.url}")
    
    return saved_images


@router.post("/variants/{variant_id}/images", response_model=List[ProductImageSchema])
async def upload_variant_images(
    variant_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> List[ProductImageSchema]:
    """
    Upload multiple images for a product variant.
    Max 1MB per image, only JPG, JPEG, PNG allowed.
    """
    # Verify variant exists
    variant = await db.get(ProductVariant, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one image file is required")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed per upload")
    
    saved_images = []
    
    for idx, file in enumerate(files):
        try:
            # Save image file
            relative_path = await save_product_image(file, variant.product_id, variant_id)
            # Store relative path (without leading slash) so frontend can construct full URL
            image_url = relative_path.replace('\\', '/')
            
            # Create ProductImage record
            product_image = ProductImage(
                product_id=variant.product_id,
                variant_id=variant_id,
                url=image_url,
                is_main=(idx == 0)  # First image is main by default
            )
            db.add(product_image)
            saved_images.append(product_image)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error uploading {file.filename}: {str(e)}")
    
    await db.commit()
    
    # Refresh images to return with IDs and ensure they're linked
    for img in saved_images:
        await db.refresh(img)
        print(f"Saved variant image {img.id}: product_id={img.product_id}, variant_id={img.variant_id}, url={img.url}")
    
    return saved_images


@router.delete("/images/{image_id}", response_model=dict)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> dict:
    """
    Delete a product image.
    """
    image = await db.get(ProductImage, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete file from storage
    try:
        # Extract relative path from URL
        url_path = image.url.replace("/uploads/", "uploads/")
        await delete_product_image(url_path)
    except Exception as e:
        # Log error but continue with DB deletion
        print(f"Error deleting image file: {e}")
    
    # Delete from database
    await db.delete(image)
    await db.commit()
    
    return {"msg": "Image deleted successfully"}


@router.patch("/images/{image_id}/set-main", response_model=ProductImageSchema)
async def set_main_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> ProductImageSchema:
    """
    Set an image as the main image for a product/variant.
    """
    image = await db.get(ProductImage, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Find all images for the same product/variant and unset main
    if image.variant_id:
        stmt = select(ProductImage).filter(ProductImage.variant_id == image.variant_id)
    else:
        stmt = select(ProductImage).filter(
            ProductImage.product_id == image.product_id,
            ProductImage.variant_id.is_(None)
        )
    
    result = await db.execute(stmt)
    all_images = result.scalars().all()
    
    for img in all_images:
        img.is_main = (img.id == image_id)
    
    await db.commit()
    await db.refresh(image)
    
    return image
