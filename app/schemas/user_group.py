from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class PermissionBase(BaseModel):
    name: str
    codename: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class UserGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class UserGroupCreate(UserGroupBase):
    permission_ids: Optional[List[int]] = []

class UserGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class UserGroup(UserGroupBase):
    id: int
    permissions: List[Permission] = []
    
    model_config = ConfigDict(from_attributes=True)
