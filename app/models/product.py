from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
if TYPE_CHECKING:
    from app.models.review import Review
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    JSON,
    DECIMAL,
    DateTime
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import Base

class Category(Base):
    name: Mapped[str] = mapped_column(String, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # FontAwesome icon class name
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id"), nullable=True)
    
    # Self-referential relationship
    parent: Mapped[Optional["Category"]] = relationship("Category", remote_side="Category.id", back_populates="subcategories")
    subcategories: Mapped[List["Category"]] = relationship("Category", back_populates="parent", lazy="selectin")
    
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")

class Product(Base):
    name: Mapped[str] = mapped_column(String, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    
    # Flash Deal fields
    is_flash_deal: Mapped[bool] = mapped_column(Boolean, default=False)
    flash_deal_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    flash_deal_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    flash_deal_price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    
    # Discount fields
    discount_percentage: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)  # 0-100
    discount_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)  # Fixed discount amount
    
    # Trending field
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)  # Track views for trending calculation
    
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan", lazy="selectin")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", primaryjoin="Product.id == ProductImage.product_id", cascade="all, delete-orphan", lazy="selectin")

class ProductVariant(Base):
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    sku: Mapped[str] = mapped_column(String, unique=True, index=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2)) # Using DECIMAL for currency
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    # JSON for flexible attributes (e.g., {"color": "red", "size": "L"})
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="variant", cascade="all, delete-orphan", lazy="selectin")

class ProductImage(Base):
    variant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("productvariant.id"), nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product.id"), nullable=True) # Fallback if image belongs to product generally
    url: Mapped[str] = mapped_column(String)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    
    variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant", back_populates="images")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="images")