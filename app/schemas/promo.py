from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator, field_serializer


class PromoCodeBase(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str = "percentage"  # "percentage" or "fixed"
    discount_value: Decimal
    min_purchase_amount: Optional[Decimal] = None
    max_discount_amount: Optional[Decimal] = None
    usage_limit: Optional[int] = None
    is_active: bool = True
    valid_from: datetime
    valid_until: datetime

    @field_validator('code')
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Promo code is required')
        return v.strip()

    @field_validator('discount_type')
    @classmethod
    def validate_discount_type(cls, v):
        if v not in ['percentage', 'fixed']:
            raise ValueError('discount_type must be either "percentage" or "fixed"')
        return v


class PromoCodeCreate(PromoCodeBase):
    pass


class PromoCodeUpdate(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    min_purchase_amount: Optional[Decimal] = None
    max_discount_amount: Optional[Decimal] = None
    usage_limit: Optional[int] = None
    is_active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class PromoCode(PromoCodeBase):
    id: int
    used_count: int

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('valid_from', 'valid_until')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat() if dt is not None else None

    @field_serializer('discount_value', 'min_purchase_amount', 'max_discount_amount')
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[float]:
        if v is None:
            return None
        return float(v)


class PromoCodeValidate(BaseModel):
    code: str
    total_amount: Decimal


class PromoCodeValidationResult(BaseModel):
    valid: bool
    discount_amount: Optional[Decimal] = None
    message: Optional[str] = None
    promo_code: Optional[PromoCode] = None
