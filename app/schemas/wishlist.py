from typing import List
from pydantic import ConfigDict
from app.schemas.product import ProductVariant
from pydantic import BaseModel
from datetime import datetime

class WishlistItemBase(BaseModel):
    product_variant_id: int

class WishlistItemCreate(WishlistItemBase):
    pass

class WishlistItem(WishlistItemBase):
    id: int
    wishlist_id: int
    variant: ProductVariant
    # added_at: datetime # If we added this to model, include here

    model_config = ConfigDict(from_attributes=True)

class WishlistBase(BaseModel):
    pass

class Wishlist(WishlistBase):
    id: int
    user_id: int
    items: List[WishlistItem] = []

    model_config = ConfigDict(from_attributes=True)
