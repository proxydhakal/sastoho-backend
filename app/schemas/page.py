from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer

class PageBase(BaseModel):
    title: str
    slug: str
    content: str
    meta_description: Optional[str] = None
    is_published: bool = True
    show_in_footer: bool = False
    footer_order: int = 0
    page_type: str = "page"

class PageCreate(PageBase):
    pass

class PageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None
    show_in_footer: Optional[bool] = None
    footer_order: Optional[int] = None
    page_type: Optional[str] = None

class Page(PageBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: Optional[datetime], _info) -> Optional[str]:
        if value is None:
            return None
        return value.isoformat()
