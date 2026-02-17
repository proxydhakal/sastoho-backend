from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_serializer

# Token (kept for API clients that use Bearer; cookies used by frontend)
class Token(BaseModel):
    access_token: str
    token_type: str


class LoginResponse(BaseModel):
    """Returned on login. Tokens in Set-Cookie and optionally in body for clients that send Bearer."""
    user: "User"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# User Group Schema for nested response
class UserGroupSimple(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# User
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    group_ids: Optional[List[int]] = []

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    group_ids: Optional[List[int]] = None

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class UserInDBBase(UserBase):
    id: int
    is_superuser: bool = False
    is_verified: bool = False
    role: str
    created_at: Optional[datetime] = None

    @field_serializer('created_at')
    def serialize_datetime(self, value: Optional[datetime], _info) -> Optional[str]:
        if value is None:
            return None
        return value.isoformat()

    model_config = ConfigDict(from_attributes=True)

class User(UserInDBBase):
    groups: List[UserGroupSimple] = []


LoginResponse.model_rebuild()

class UserInDB(UserInDBBase):
    hashed_password: str
