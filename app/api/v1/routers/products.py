from typing import Any, List, Union
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_current_active_user, get_current_admin_user
from app.core.database import get_db
from app.core.storage import save_category_image
from app.core.query_params import str_to_bool
from app.core.config import settings
from app.schemas.product import Category, CategoryCreate, CategoryUpdate, Product, ProductCreate, ProductUpdate
from app.services.product_service import category_service, product_service
from app.models.user import User

router = APIRouter()

# --- Categories ---

@router.get("/categories", response_model=List[Category])
async def read_categories(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieve categories (top-level with subcategories). Optional search by name or slug.
    """
    categories = await category_service.get_multi_with_subcategories(
        db, skip=skip, limit=limit, search=search
    )
    return categories

@router.post("/categories", response_model=Category)
async def create_category(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Create new category.
    """
    category = await category_service.create_with_slug(db, obj_in=category_in)
    return category

@router.get("/categories/{slug}", response_model=Category)
async def get_category_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get category by slug."""
    category = await category_service.get_by_slug(db, slug=slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.patch("/categories/{slug}", response_model=Category)
async def update_category(
    slug: str,
    category_in: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    category = await category_service.get_by_slug(db, slug=slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category = await category_service.update(db, db_obj=category, obj_in=category_in)
    return category

@router.post("/categories/{slug}/upload-image", response_model=Category)
async def upload_category_image(
    slug: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """Upload category image."""
    category = await category_service.get_by_slug(db, slug=slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    relative_path = await save_category_image(file, category.id)
    category.image_url = relative_path.replace("\\", "/")
    await db.commit()
    await db.refresh(category)
    return category

@router.delete("/categories/{slug}", response_model=dict)
async def delete_category(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    category = await category_service.get_by_slug(db, slug=slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await category_service.remove(db, id=category.id)
    return {"msg": "Category deleted successfully"}

# --- Products ---

@router.get("/products", response_model=List[Product])
async def read_products(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    category_id: int = None,
    category_slug: str = None,
    flash_deals_only: Union[str, bool, int] = Query(False, description="Filter flash deals only. Accepts: 1/0, true/false"),
    trending_only: Union[str, bool, int] = Query(False, description="Filter trending products only. Accepts: 1/0, true/false"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieve products with optional filtering.
    Query parameters flash_deals_only and trending_only accept: "1"/"0", "true"/"false", or boolean values.
    In production (MySQL), these are converted to 1/0 for database storage.
    """
    # Convert query parameters to boolean (handles "1"/"0", "true"/"false", etc.)
    flash_deals_bool = str_to_bool(flash_deals_only)
    trending_bool = str_to_bool(trending_only)
    
    # Debug logging (remove in production if needed)
    if settings.DEBUG:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Product filter - flash_deals_only: {flash_deals_only} -> {flash_deals_bool}, trending_only: {trending_only} -> {trending_bool}")
    
    products = await product_service.get_multi_with_filtering(
        db, 
        skip=skip, 
        limit=limit, 
        search=search, 
        category_id=category_id,
        category_slug=category_slug,
        flash_deals_only=flash_deals_bool,
        trending_only=trending_bool
    )
    # Debug: Log image data for first few products
    for p in products[:5]:
        if hasattr(p, 'images'):
            print(f"Product {p.id}: {len(p.images)} product images, {len(p.variants)} variants")
            for v in p.variants:
                print(f"  Variant {v.id}: {len(v.images)} variant images")
    return products

@router.post("/products", response_model=Product)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Create new product.
    """
    product = await product_service.create_with_variants(db, obj_in=product_in)
    return product

@router.get("/products/{slug}", response_model=Product)
async def read_product(
    slug: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get product by slug. Increments view count for trending calculation.
    """
    product = await product_service.get_by_slug(db, slug=slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Increment view count for trending calculation
    await product_service.increment_view_count(db, product.id)
    return product

@router.patch("/products/{slug}", response_model=Product)
async def update_product(
    slug: str,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """Update product by slug."""
    product = await product_service.get_by_slug(db, slug=slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = await product_service.update(db, db_obj=product, obj_in=product_in)
    return product

@router.delete("/products/{slug}", response_model=dict)
async def delete_product(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Soft delete a product.
    """
    product = await product_service.get_by_slug(db, slug=slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await product_service.soft_delete(db, id=product.id)
    return {"msg": "Product deleted successfully"}

@router.patch("/variants/{sku}/inventory", response_model=dict)
async def update_variant_inventory(
    sku: str,
    quantity: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update stock quantity for a variant.
    """
    variant = await product_service.update_variant_stock(db, sku=sku, quantity=quantity)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return {"sku": variant.sku, "stock_quantity": variant.stock_quantity}
