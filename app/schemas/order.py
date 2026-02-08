from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator

# --- Order Item (variant nested for product name in responses) ---
class OrderItemBase(BaseModel):
    product_variant_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class ProductNameForOrder(BaseModel):
    name: str
    slug: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductVariantForOrder(BaseModel):
    id: int
    product_id: int
    sku: str
    price: Decimal
    product: Optional[ProductNameForOrder] = None

    model_config = ConfigDict(from_attributes=True)


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    price_at_purchase: Decimal
    variant: Optional[ProductVariantForOrder] = None

    model_config = ConfigDict(from_attributes=True)

# --- Order ---
class OrderBase(BaseModel):
    shipping_address: Optional[dict] = None  # Snapshot when using custom address; optional if shipping_address_id provided
    shipping_address_id: Optional[int] = None  # Reference to Address model
    billing_address_id: Optional[int] = None

class OrderCreate(OrderBase):
    # Payment method: cod, esewa, khalti, card
    payment_method: str = "cod"
    # Payment method ID (Stripe token etc.); not required for COD
    payment_method_id: Optional[str] = None
    # Optional voucher/promo code (validated server-side)
    promo_code: Optional[str] = None 

class OrderUpdate(BaseModel):
    status: str 

class Order(OrderBase):
    id: int
    user_id: int
    order_number: Optional[str] = None
    status: str
    total_amount: Decimal
    stripe_payment_id: Optional[str] = None
    payment_method: Optional[str] = None
    promo_code_id: Optional[int] = None
    discount_amount: Optional[Decimal] = None
    created_at: datetime
    items: List[OrderItem] = []

    model_config = ConfigDict(from_attributes=True)


class OrderAdmin(Order):
    """Order response for admin: includes customer name and email from user."""
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
