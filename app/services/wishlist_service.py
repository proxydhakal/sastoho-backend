from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.wishlist import Wishlist, WishlistItem

class WishlistService:
    async def get_wishlist(self, db: AsyncSession, user_id: int) -> Wishlist:
        stmt = select(Wishlist).filter(Wishlist.user_id == user_id).options(selectinload(Wishlist.items).selectinload(WishlistItem.variant))
        result = await db.execute(stmt)
        wishlist = result.scalars().first()
        
        if not wishlist:
            wishlist = Wishlist(user_id=user_id)
            db.add(wishlist)
            await db.commit()
            # No items yet, so simple refresh or manual construction is fine, 
            # but sticking to pattern for safety
            db.expire_all()
            stmt = select(Wishlist).filter(Wishlist.user_id == user_id).options(selectinload(Wishlist.items).selectinload(WishlistItem.variant))
            result = await db.execute(stmt)
            return result.scalars().first()
        
        return wishlist

    async def add_item(self, db: AsyncSession, user_id: int, variant_id: int) -> Wishlist:
        wishlist = await self.get_wishlist(db, user_id)
        
        # Check duplicate
        if any(item.product_variant_id == variant_id for item in wishlist.items):
            return wishlist
        
        new_item = WishlistItem(wishlist_id=wishlist.id, product_variant_id=variant_id)
        db.add(new_item)
        
        wishlist_id = wishlist.id
        await db.commit()
        
        db.expire_all()
        stmt = select(Wishlist).filter(Wishlist.id == wishlist_id).options(selectinload(Wishlist.items).selectinload(WishlistItem.variant))
        result = await db.execute(stmt)
        return result.scalars().first()

    async def remove_item(self, db: AsyncSession, user_id: int, variant_id: int) -> Wishlist:
        wishlist = await self.get_wishlist(db, user_id)
        item = next((i for i in wishlist.items if i.product_variant_id == variant_id), None)
        
        if item:
            await db.delete(item)
            wishlist_id = wishlist.id
            await db.commit()
            
            db.expire_all()
            stmt = select(Wishlist).filter(Wishlist.id == wishlist_id).options(selectinload(Wishlist.items).selectinload(WishlistItem.variant))
            result = await db.execute(stmt)
            return result.scalars().first()
            
        return wishlist

wishlist_service = WishlistService()
