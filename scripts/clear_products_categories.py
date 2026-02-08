"""
Script to clear Product and Category tables.
Run with: python scripts/clear_products_categories.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete
from app.core.database import SessionLocal
from app.models.product import Product, Category, ProductVariant, ProductImage
from app.models.cart import Cart, CartItem
from app.models.wishlist import Wishlist, WishlistItem
from app.models.order import Order, OrderItem
from app.models.review import Review


async def clear_tables():
    """Clear Product and Category tables."""
    async with SessionLocal() as db:
        try:
            # Delete in correct order due to foreign keys
            # (Cart/Wishlist/Orders/Reviews reference product variants/products)
            print("Deleting cart items...")
            await db.execute(delete(CartItem))
            print("Deleting carts...")
            await db.execute(delete(Cart))

            print("Deleting wishlist items...")
            await db.execute(delete(WishlistItem))
            print("Deleting wishlists...")
            await db.execute(delete(Wishlist))

            print("Deleting order items...")
            await db.execute(delete(OrderItem))
            print("Deleting orders...")
            await db.execute(delete(Order))

            print("Deleting reviews...")
            await db.execute(delete(Review))

            print("Deleting product images...")
            await db.execute(delete(ProductImage))
            
            print("Deleting product variants...")
            await db.execute(delete(ProductVariant))
            
            print("Deleting products...")
            await db.execute(delete(Product))
            
            print("Deleting categories...")
            await db.execute(delete(Category))
            
            await db.commit()
            print("Successfully cleared Product and Category tables.")
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    print("WARNING: This will delete ALL products and categories!")
    response = input("Type 'yes' to continue: ")
    if response.lower() == 'yes':
        asyncio.run(clear_tables())
    else:
        print("Cancelled.")
