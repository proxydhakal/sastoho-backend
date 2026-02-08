from typing import List, Optional
from pydantic import ConfigDict, UUID4
from app.schemas.product import ProductVariant, ProductImage
from pydantic import BaseModel

# Brief product for cart display (slug, name, images)
class ProductBrief(BaseModel):
    id: int
    slug: str
    name: str
    images: List[ProductImage] = []

    model_config = ConfigDict(from_attributes=True)

# Variant with nested product for cart response
class ProductVariantWithProduct(ProductVariant):
    product: Optional[ProductBrief] = None

    model_config = ConfigDict(from_attributes=True)

class CartItemBase(BaseModel):
    product_variant_id: int
    quantity: int = 1

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItem(CartItemBase):
    id: int
    cart_id: int
    variant: ProductVariantWithProduct  # Nested variant with product details

    model_config = ConfigDict(from_attributes=True)

class CartBase(BaseModel):
    session_id: Optional[str] = None

class CartCreate(CartBase):
    pass

class Cart(CartBase):
    id: int = 0
    user_id: Optional[int] = None
    items: List[CartItem] = []

    model_config = ConfigDict(from_attributes=True)
