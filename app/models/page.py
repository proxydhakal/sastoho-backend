from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Page(Base):
    __tablename__ = "page"

    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Rich text HTML content
    meta_description: Mapped[str] = mapped_column(String, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    show_in_footer: Mapped[bool] = mapped_column(Boolean, default=False)
    footer_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Order in footer
    page_type: Mapped[str] = mapped_column(String, default="page")  # page, policy, help, etc.
