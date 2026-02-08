from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from decimal import Decimal

# --- Product Image ---
class ProductImageBase(BaseModel):
    url: str
    is_main: bool = False

class ProductImageCreate(ProductImageBase):
    pass

class ProductImage(ProductImageBase):
    id: int
    product_id: Optional[int]
    variant_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)

# --- Product Variant ---
class ProductVariantBase(BaseModel):
    sku: str
    price: Decimal
    stock_quantity: int = 0
    attributes: Optional[Dict[str, Any]] = None

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariant(ProductVariantBase):
    id: int
    product_id: int
    images: List[ProductImage] = []

    model_config = ConfigDict(from_attributes=True)

# --- Product ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    category_id: int
    # Flash Deal fields
    is_flash_deal: bool = False
    flash_deal_start: Optional[datetime] = None
    flash_deal_end: Optional[datetime] = None
    flash_deal_price: Optional[Decimal] = None
    # Discount fields
    discount_percentage: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    # Trending field
    is_trending: bool = False
    view_count: int = 0

class ProductCreate(ProductBase):
    # Optionally accept variants during creation
    variants: List[ProductVariantCreate] = []

    @field_validator('variants', mode='before')
    @classmethod
    def ensure_variants_list(cls, v):
        return v or []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    is_flash_deal: Optional[bool] = None
    flash_deal_start: Optional[datetime] = None
    flash_deal_end: Optional[datetime] = None
    flash_deal_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    is_trending: Optional[bool] = None
    view_count: Optional[int] = None


class Product(ProductBase):
    id: int
    slug: str
    variants: List[ProductVariant] = []
    images: List[ProductImage] = []

    model_config = ConfigDict(from_attributes=True)

# --- Category ---
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None  # FontAwesome icon class name (e.g., "fa fa-box", "fas fa-tshirt")
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    slug: str
    subcategories: List["Category"] = []

    model_config = ConfigDict(from_attributes=True)

Category.model_rebuild()
