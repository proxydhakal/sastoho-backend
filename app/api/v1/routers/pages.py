from typing import Any, List, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.page import Page

from app.api.v1.dependencies.auth import get_current_active_user, get_current_user_optional
from app.core.database import get_db
from app.core.storage import save_content_image
from app.core.query_params import str_to_bool
from app.models.user import User
from app.schemas.page import Page, PageCreate, PageUpdate
from app.services.page_service import page_service

router = APIRouter()

@router.get("/", response_model=List[Page])
async def get_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    published_only: Union[str, bool, int] = Query(True, description="Filter published pages only. Accepts: 1/0, true/false"),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Any:
    """
    Get all pages. Published only by default for non-authenticated users. Optional search by title or slug.
    Query parameter published_only accepts: "1"/"0", "true"/"false", or boolean values.
    In production (MySQL), these are converted to 1/0 for database storage.
    """
    # Convert query parameter to boolean (handles "1"/"0", "true"/"false", etc.)
    published_only_bool = str_to_bool(published_only)
    
    # If user is admin, allow seeing unpublished pages
    if current_user and current_user.is_superuser:
        published_only_bool = False

    pages = await page_service.get_all(
        db, skip=skip, limit=limit, published_only=published_only_bool, search=search
    )
    return pages

@router.get("/footer", response_model=List[Page])
async def get_footer_pages(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all pages that should be shown in the footer.
    """
    pages = await page_service.get_footer_pages(db)
    return pages

@router.get("/{slug}", response_model=Page)
async def get_page_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Any:
    """
    Get a page by its slug. Only published pages for non-authenticated users.
    """
    page = await page_service.get_by_slug(db, slug)
    if not page:
        # If user is admin, try to get unpublished page
        if current_user and current_user.is_superuser:
            stmt = select(Page).filter(Page.slug == slug)
            result = await db.execute(stmt)
            page = result.scalars().first()
        
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
    
    return page

@router.post("/upload-image")
async def upload_page_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Upload an image for page content (rich text editor). Admin only.
    Returns the full URL path for the uploaded image.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    relative_path = await save_content_image(file)
    url_path = "/" + relative_path.replace("\\", "/")
    return {"url": url_path}


@router.post("/", response_model=Page, status_code=201)
async def create_page(
    page_in: PageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new page. Admin only.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    page = await page_service.create_page(db, page_in)
    return page

@router.patch("/{page_id}", response_model=Page)
async def update_page(
    page_id: int,
    page_in: PageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a page. Admin only.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    page = await page_service.update_page(db, page_id, page_in)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.delete("/{page_id}")
async def delete_page(
    page_id: int,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a page. Admin only.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    success = await page_service.delete_page(db, page_id)
    if not success:
        raise HTTPException(status_code=404, detail="Page not found")
    response.status_code = 204
