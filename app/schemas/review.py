from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# --- Review ---
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class UserInfo(BaseModel):
    id: int
    full_name: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)

class ProductInfo(BaseModel):
    id: int
    name: str
    slug: str
    
    model_config = ConfigDict(from_attributes=True)

class ReviewOut(ReviewBase):
    id: int
    user_id: int
    product_id: int
    created_at: datetime
    is_approved: bool
    user: Optional[UserInfo] = None
    product: Optional[ProductInfo] = None
    
    model_config = ConfigDict(from_attributes=True)
