from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.product import Category, Product, ProductVariant, ProductImage
from app.schemas.product import CategoryCreate, ProductCreate, CategoryUpdate, ProductUpdate
from app.crud.base import CRUDBase

# Slugify helper
import re
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

async def generate_unique_slug(db: AsyncSession, base_slug: str, model_class, exclude_id: Optional[int] = None) -> str:
    """Generate a unique slug by appending a number if needed."""
    slug = base_slug
    counter = 1
    while True:
        stmt = select(model_class).filter(model_class.slug == slug)
        if exclude_id:
            stmt = stmt.filter(model_class.id != exclude_id)
        result = await db.execute(stmt)
        if not result.scalars().first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1

from sqlalchemy import or_

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryCreate]):
    async def get_multi_with_subcategories(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Category]:
        # Only fetch top-level categories (parent_id is None) and eager load subcategories
        stmt = (
            select(Category)
            .filter(Category.parent_id == None)
            .options(selectinload(Category.subcategories))
        )
        if search and search.strip():
            q = f"%{search.strip()}%"
            stmt = stmt.filter(or_(Category.name.ilike(q), Category.slug.ilike(q)))
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_with_slug(self, db: AsyncSession, *, obj_in: CategoryCreate) -> Category:
        base_slug = slugify(obj_in.name)
        unique_slug = await generate_unique_slug(db, base_slug, Category)
        db_obj = Category(
            name=obj_in.name,
            description=obj_in.description,
            parent_id=obj_in.parent_id,
            image_url=obj_in.image_url,
            icon=obj_in.icon,
            slug=unique_slug
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: Category, obj_in: CategoryUpdate) -> Category:
        update_data = obj_in.model_dump(exclude_unset=True)
        # If name is updated, regenerate slug
        if 'name' in update_data and update_data['name'] != db_obj.name:
            base_slug = slugify(update_data['name'])
            update_data['slug'] = await generate_unique_slug(db, base_slug, Category, exclude_id=db_obj.id)
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
    
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Category]:
        stmt = select(Category).filter(Category.slug == slug)
        result = await db.execute(stmt)
        return result.scalars().first()
        
    async def remove(self, db: AsyncSession, *, id: int) -> Category:
        obj = await self.get(db, id)
        if obj:
            # Try soft delete, fallback to hard delete if column doesn't exist
            # TODO: After running migration b55f5ee61a4c, this will use soft delete
            try:
                obj.is_deleted = True
                db.add(obj)
                await db.commit()
            except (AttributeError, Exception):
                # Column doesn't exist yet, use hard delete
                await db.delete(obj)
                await db.commit()
        return obj

class CRUDProduct(CRUDBase[Product, ProductCreate, ProductCreate]):
    async def create_with_variants(self, db: AsyncSession, *, obj_in: ProductCreate) -> Product:
        base_slug = slugify(obj_in.name)
        unique_slug = await generate_unique_slug(db, base_slug, Product)
        db_obj = Product(
            name=obj_in.name,
            description=obj_in.description,
            is_active=obj_in.is_active,
            category_id=obj_in.category_id,
            slug=unique_slug,
            # Flash Deal fields
            is_flash_deal=obj_in.is_flash_deal,
            flash_deal_start=obj_in.flash_deal_start,
            flash_deal_end=obj_in.flash_deal_end,
            flash_deal_price=obj_in.flash_deal_price,
            # Discount fields
            discount_percentage=obj_in.discount_percentage,
            discount_amount=obj_in.discount_amount,
            # Trending field
            is_trending=obj_in.is_trending,
            view_count=obj_in.view_count,
        )
        db.add(db_obj)
        
        # Flush to get ID
        await db.flush()
        
        # Add variants
        for variant_in in obj_in.variants:
            db_variant = ProductVariant(
                product_id=db_obj.id,
                sku=variant_in.sku,
                price=variant_in.price,
                stock_quantity=variant_in.stock_quantity,
                attributes=variant_in.attributes
            )
            db.add(db_variant)
            
        await db.commit()
        
        # Explicitly fetch with relationships to ensure they are loaded/greenlet safe
        stmt = (
            select(Product)
            .filter(Product.id == db_obj.id)
            .options(
                selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Product.images)
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def update(self, db: AsyncSession, *, db_obj: Product, obj_in: ProductUpdate) -> Product:
        update_data = obj_in.model_dump(exclude_unset=True)
        # If name is updated, regenerate slug
        if 'name' in update_data and update_data['name'] != db_obj.name:
            base_slug = slugify(update_data['name'])
            update_data['slug'] = await generate_unique_slug(db, base_slug, Product, exclude_id=db_obj.id)
        # Update scalar fields
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Product]:
        stmt = (
            select(Product)
            .filter(Product.slug == slug)
            .options(selectinload(Product.variants).selectinload(ProductVariant.images))
        )
        result = await db.execute(stmt)
        return result.scalars().first()



    async def get_with_variants(self, db: AsyncSession, id: Any) -> Optional[Product]:
        # Note: is_deleted filter removed temporarily - add back after running migration b55f5ee61a4c
        stmt = (
            select(Product)
            .filter(Product.id == id)
            .options(selectinload(Product.variants).selectinload(ProductVariant.images))
        )
        result = await db.execute(stmt)
        return result.scalars().first()
    
    async def get_multi_with_filtering(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        flash_deals_only: bool = False,
        trending_only: bool = False
    ) -> List[Product]:
        # Note: is_deleted filter removed temporarily - add back after running migration b55f5ee61a4c
        # Load variants, their images, and product-level images
        from app.models.product import ProductImage
        from datetime import datetime, timezone
        stmt = select(Product).options(
            selectinload(Product.variants).selectinload(ProductVariant.images),
            selectinload(Product.images)
        )
        # Use .is_(True) for MySQL boolean compatibility (converts to = 1)
        stmt = stmt.filter(Product.is_active.is_(True))

        if category_id:
            stmt = stmt.filter(Product.category_id == category_id)
        elif category_slug:
            category = await category_service.get_by_slug(db, slug=category_slug)
            if category:
                stmt = stmt.filter(Product.category_id == category.id)
        
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
            stmt = stmt.filter(search_filter)
        
        if flash_deals_only:
            now = datetime.now(timezone.utc)
            stmt = stmt.filter(
                Product.is_flash_deal.is_(True),
                Product.flash_deal_start <= now,
                Product.flash_deal_end >= now
            )
            stmt = stmt.order_by(Product.flash_deal_end.asc())  # Ending soon first

        if trending_only:
            stmt = stmt.filter(Product.is_trending.is_(True))
            stmt = stmt.order_by(Product.view_count.desc())

        # Default: latest first (by created_at)
        if not flash_deals_only and not trending_only:
            stmt = stmt.order_by(Product.created_at.desc())
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def increment_view_count(self, db: AsyncSession, product_id: int) -> None:
        """Increment view count for a product (for trending calculation)."""
        product = await self.get(db, id=product_id)
        if product:
            product.view_count = (product.view_count or 0) + 1
            db.add(product)
            await db.commit()

    async def soft_delete(self, db: AsyncSession, id: int) -> Optional[Product]:
        product = await self.get(db, id)
        if product:
            # Try soft delete, fallback to hard delete if column doesn't exist
            # TODO: After running migration b55f5ee61a4c, this will use soft delete
            try:
                product.is_deleted = True
                db.add(product)
                await db.commit()
            except (AttributeError, Exception):
                # Column doesn't exist yet, use hard delete
                await db.delete(product)
                await db.commit()
        return product

    async def update_variant_stock(self, db: AsyncSession, sku: str, quantity: int) -> Optional[ProductVariant]:
        stmt = select(ProductVariant).filter(ProductVariant.sku == sku)
        result = await db.execute(stmt)
        variant = result.scalars().first()
        if variant:
            variant.stock_quantity = quantity
            db.add(variant)
            await db.commit()
            await db.refresh(variant)
        return variant

category_service = CRUDCategory(Category)
product_service = CRUDProduct(Product)
