import os
import io
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles

# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
}

# Site assets: logo (png/jpg), favicon (png/jpg/svg/ico)
ALLOWED_SITE_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
}

# Max file size: 1MB
MAX_FILE_SIZE = 1024 * 1024  # 1MB in bytes
MAX_FAVICON_SIZE = 512 * 1024  # 512KB for favicon
MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2MB for logo

# Base directory for uploads
UPLOAD_DIR = Path("uploads")
PRODUCT_IMAGES_DIR = UPLOAD_DIR / "products"
SITE_ASSETS_DIR = UPLOAD_DIR / "site"
CATEGORY_IMAGES_DIR = UPLOAD_DIR / "categories"
PAGE_CONTENT_DIR = UPLOAD_DIR / "pages"

# Ensure directories exist
PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
SITE_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
CATEGORY_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
PAGE_CONTENT_DIR.mkdir(parents=True, exist_ok=True)


def validate_image_file(file: UploadFile) -> None:
    """Validate image file type and size."""
    # Check file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: JPG, JPEG, PNG"
        )
    
    # Note: File size validation will be done when reading the file
    # since UploadFile doesn't provide size directly


async def save_product_image(file: UploadFile, product_id: int, variant_id: Optional[int] = None) -> str:
    """
    Save uploaded product image and return the file path.
    
    Args:
        file: Uploaded file
        product_id: Product ID
        variant_id: Optional variant ID
    
    Returns:
        Relative file path from project root
    """
    # Validate file
    validate_image_file(file)
    
    # Read file content to check size
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds 1MB limit. Current size: {len(content) / 1024:.2f}KB"
        )
    
    # Validate it's actually an image
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    
    # Generate unique filename
    file_ext = ALLOWED_IMAGE_TYPES[file.content_type]
    filename = f"{uuid.uuid4()}{file_ext}"
    
    # Create product-specific directory
    product_dir = PRODUCT_IMAGES_DIR / str(product_id)
    if variant_id:
        product_dir = product_dir / "variants" / str(variant_id)
    product_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = product_dir / filename
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Return relative path (for URL generation)
    relative_path = f"uploads/products/{product_id}"
    if variant_id:
        relative_path += f"/variants/{variant_id}"
    relative_path += f"/{filename}"
    
    return relative_path


def get_image_url(relative_path: str, base_url: str = "/") -> str:
    """Convert relative file path to URL."""
    # Remove leading slash if present to avoid double slashes
    relative_path = relative_path.lstrip('/')
    return f"{base_url.rstrip('/')}/{relative_path.replace('\\', '/')}"


async def delete_product_image(file_path: str) -> None:
    """Delete product image file."""
    full_path = Path(file_path)
    if full_path.exists():
        full_path.unlink()
        # Try to remove empty parent directories
        try:
            full_path.parent.rmdir()
            if full_path.parent.parent.name == "variants":
                full_path.parent.parent.rmdir()
        except OSError:
            pass  # Directory not empty or doesn't exist


async def save_site_asset(file: UploadFile, asset_type: str) -> str:
    """
    Save uploaded site asset (logo or favicon).
    Args:
        file: Uploaded file
        asset_type: "logo" or "favicon"
    Returns:
        Relative path (e.g., uploads/site/logo_xxx.png)
    """
    if asset_type not in ("logo", "favicon"):
        raise HTTPException(status_code=400, detail="asset_type must be 'logo' or 'favicon'")
    if file.content_type not in ALLOWED_SITE_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: JPG, PNG, SVG, ICO"
        )
    content = await file.read()
    max_size = MAX_LOGO_SIZE if asset_type == "logo" else MAX_FAVICON_SIZE
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {max_size // 1024}KB limit"
        )
    ext = ALLOWED_SITE_IMAGE_TYPES.get(file.content_type, ".png")
    filename = f"{asset_type}_{uuid.uuid4()}{ext}"
    file_path = SITE_ASSETS_DIR / filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    return f"uploads/site/{filename}"


async def save_content_image(file: UploadFile) -> str:
    """
    Save uploaded content/page image (for rich text editors).
    Returns relative path (e.g., uploads/pages/uuid.jpg).
    """
    validate_image_file(file)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds 1MB limit. Current size: {len(content) / 1024:.2f}KB",
        )
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    ext = ALLOWED_IMAGE_TYPES.get(file.content_type, ".png")
    filename = f"{uuid.uuid4()}{ext}"
    file_path = PAGE_CONTENT_DIR / filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    return f"uploads/pages/{filename}"


async def delete_site_asset(relative_path: str) -> None:
    """Delete site asset file."""
    full_path = Path(relative_path)
    if full_path.exists():
        full_path.unlink()


async def save_category_image(file: UploadFile, category_id: int) -> str:
    """
    Save uploaded category image.
    Args:
        file: Uploaded file
        category_id: Category ID
    Returns:
        Relative path (e.g., uploads/categories/category_xxx.png)
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: JPG, PNG"
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {MAX_FILE_SIZE // 1024}KB limit"
        )
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    ext = ALLOWED_IMAGE_TYPES.get(file.content_type, ".png")
    filename = f"category_{category_id}_{uuid.uuid4()}{ext}"
    file_path = CATEGORY_IMAGES_DIR / filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    return f"uploads/categories/{filename}"
