from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product, ProductVariant
from app.schemas.cart import CartItemCreate, CartItemUpdate

class CartService:
    async def get_cart(self, db: AsyncSession, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Optional[Cart]:
        stmt = select(Cart).options(
            selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product).selectinload(Product.images)
        )
        
        if user_id:
            stmt = stmt.filter(Cart.user_id == user_id)
        elif session_id:
            stmt = stmt.filter(Cart.session_id == session_id)
        else:
            return None
            
        result = await db.execute(stmt)
        return result.scalars().first()

    async def create_cart(self, db: AsyncSession, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Cart:
        cart = Cart(user_id=user_id, session_id=session_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
        return cart

    async def add_item(self, db: AsyncSession, variant_id: int, quantity: int, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Cart:
        cart = await self.get_cart(db, user_id, session_id)
        if not cart:
            cart = await self.create_cart(db, user_id, session_id)
            # Re-fetch with options/greenlet safe
            stmt = select(Cart).filter(Cart.id == cart.id).options(selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product).selectinload(Product.images))
            result = await db.execute(stmt)
            cart = result.scalars().first()

        # Check if item exists
        existing_item = next((item for item in cart.items if item.product_variant_id == variant_id), None)
        
        if existing_item:
            existing_item.quantity += quantity
            db.add(existing_item)
        else:
            new_item = CartItem(cart_id=cart.id, product_variant_id=variant_id, quantity=quantity)
            db.add(new_item)
        
        cart_id = cart.id 
        await db.commit()
        
        # Force strict reload to avoid stale identity map state
        db.expire_all()
        
        stmt = select(Cart).filter(Cart.id == cart_id).options(selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product).selectinload(Product.images))
        result = await db.execute(stmt)
        return result.scalars().first()

    async def remove_item(self, db: AsyncSession, item_id: int, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Optional[Cart]:
        cart = await self.get_cart(db, user_id, session_id)
        if not cart:
            return None
            
        item = await db.get(CartItem, item_id)
        if item and item.cart_id == cart.id:
            await db.delete(item)
            cart_id = cart.id
            await db.commit()
            
            db.expire_all()
            stmt = select(Cart).filter(Cart.id == cart_id).options(selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product).selectinload(Product.images))
            result = await db.execute(stmt)
            return result.scalars().first()
        return None

    async def update_item_quantity(self, db: AsyncSession, item_id: int, quantity: int, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Optional[Cart]:
        cart = await self.get_cart(db, user_id, session_id)
        if not cart:
            return None

        item = await db.get(CartItem, item_id)
        if item and item.cart_id == cart.id:
            if quantity <= 0:
                await db.delete(item)
            else:
                item.quantity = quantity
                db.add(item)
            
            cart_id = cart.id
            await db.commit()
            
            db.expire_all()
            stmt = select(Cart).filter(Cart.id == cart_id).options(selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product).selectinload(Product.images))
            result = await db.execute(stmt)
            return result.scalars().first()
        return None

    async def merge_carts(self, db: AsyncSession, session_id: str, user_id: int) -> Cart:
        """
        Merge session cart into user cart.
        Combines quantities for matching items, moves unique items to user cart.
        """
        # Get carts with items loaded
        user_cart = await self.get_cart(db, user_id=user_id)
        session_cart = await self.get_cart(db, session_id=session_id)
        
        if not session_cart or not session_cart.items:
            # No session cart or empty session cart
            if not user_cart:
                user_cart = await self.create_cart(db, user_id=user_id)
            return user_cart

        if not user_cart:
            # If user has no cart, just assign the session cart to user and clear session_id
            session_cart.user_id = user_id
            session_cart.session_id = None
            db.add(session_cart)
            await db.commit()
            await db.refresh(session_cart)
            # Reload with relationships
            return await self.get_cart(db, user_id=user_id)
        
        # Merge items: combine quantities for matching variants, move unique items
        user_item_map = {item.product_variant_id: item for item in user_cart.items}
        
        for s_item in list(session_cart.items):  # Use list() to avoid modification during iteration
            if s_item.product_variant_id in user_item_map:
                # Item exists in user cart - merge quantities
                u_item = user_item_map[s_item.product_variant_id]
                u_item.quantity += s_item.quantity
                db.add(u_item)
                # Delete the session item
                await db.delete(s_item)
            else:
                # Item doesn't exist in user cart - move it
                s_item.cart_id = user_cart.id
                db.add(s_item)
        
        # Delete the empty session cart
        await db.delete(session_cart)
        await db.commit()
        
        # Return refreshed user cart with all relationships
        return await self.get_cart(db, user_id=user_id)

cart_service = CartService()
