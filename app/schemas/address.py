from typing import Optional
from pydantic import BaseModel, ConfigDict

class AddressBase(BaseModel):
    full_name: str
    phone_number: str
    street: str
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Nepal"
    is_default: bool = False
    address_type: str = "shipping"  # shipping or billing

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None
    address_type: Optional[str] = None

class Address(AddressBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
