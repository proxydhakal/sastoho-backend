from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.page import Page
from app.schemas.page import PageCreate, PageUpdate
import re

class PageService:
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from title."""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Page]:
        """Get a page by its slug."""
        stmt = select(Page).filter(Page.slug == slug, Page.is_published == True)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, db: AsyncSession, page_id: int) -> Optional[Page]:
        """Get a page by its ID."""
        stmt = select(Page).filter(Page.id == page_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        published_only: bool = False,
        search: Optional[str] = None,
    ) -> List[Page]:
        """Get all pages, optionally filtered by published status and search (title/slug)."""
        stmt = select(Page)
        if published_only:
            stmt = stmt.filter(Page.is_published == True)
        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.filter(
                (Page.title.ilike(term)) | (Page.slug.ilike(term))
            )
        stmt = stmt.order_by(Page.footer_order, Page.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_footer_pages(self, db: AsyncSession) -> List[Page]:
        """Get all pages that should be shown in the footer."""
        stmt = select(Page).filter(
            Page.show_in_footer == True,
            Page.is_published == True
        ).order_by(Page.footer_order, Page.title)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create_page(self, db: AsyncSession, page_in: PageCreate) -> Page:
        """Create a new page."""
        # Generate slug if not provided
        slug = page_in.slug or self._generate_slug(page_in.title)
        
        # Ensure slug is unique
        existing = await self.get_by_slug(db, slug)
        if existing:
            counter = 1
            base_slug = slug
            while existing:
                slug = f"{base_slug}-{counter}"
                existing = await self.get_by_slug(db, slug)
                counter += 1

        page = Page(
            title=page_in.title,
            slug=slug,
            content=page_in.content,
            meta_description=page_in.meta_description,
            is_published=page_in.is_published,
            show_in_footer=page_in.show_in_footer,
            footer_order=page_in.footer_order,
            page_type=page_in.page_type
        )
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page

    async def update_page(self, db: AsyncSession, page_id: int, page_in: PageUpdate) -> Optional[Page]:
        """Update a page."""
        page = await self.get_by_id(db, page_id)
        if not page:
            return None

        update_data = page_in.model_dump(exclude_unset=True)
        
        # Handle slug update - regenerate if title changed
        if 'title' in update_data and 'slug' not in update_data:
            update_data['slug'] = self._generate_slug(update_data['title'])
        
        # Ensure slug uniqueness if changed
        if 'slug' in update_data and update_data['slug'] != page.slug:
            existing = await self.get_by_slug(db, update_data['slug'])
            if existing and existing.id != page_id:
                counter = 1
                base_slug = update_data['slug']
                while existing and existing.id != page_id:
                    update_data['slug'] = f"{base_slug}-{counter}"
                    existing = await self.get_by_slug(db, update_data['slug'])
                    counter += 1

        for field, value in update_data.items():
            setattr(page, field, value)

        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page

    async def delete_page(self, db: AsyncSession, page_id: int) -> bool:
        """Delete a page."""
        page = await self.get_by_id(db, page_id)
        if not page:
            return False

        await db.delete(page)
        await db.commit()
        return True

page_service = PageService()
