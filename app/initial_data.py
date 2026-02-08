import asyncio
import logging
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.product import Category
# Import other models to ensure they are registered for relationships
from app.models.cart import Cart
from app.models.wishlist import Wishlist
from app.models.order import Order
from app.models.review import Review
from app.models.user_group import UserGroup
from app.models.permission import Permission
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_initial_data() -> None:
    async with SessionLocal() as db:
        # 1. Create Superuser
        logger.info("Creating superuser...")
        result = await db.execute(select(User).filter(User.email == "proxydhakal@gmail.com"))
        user = result.scalars().first()
        
        if not user:
            user = User(
                email="proxydhakal@gmail.com",
                hashed_password=get_password_hash("admin@123"),
                full_name="Proxy Dhakal",
                is_active=True,
                is_superuser=True,
                is_verified=True,
                role="admin"
            )
            db.add(user)
            await db.commit()
            logger.info("Superuser created")
        else:
            # Update password for existing superuser to ensure it matches CREDENTIALS.md
            user.hashed_password = get_password_hash("admin@123")
            user.is_superuser = True
            user.role = "admin"
            user.is_active = True
            db.add(user)
            await db.commit()
            logger.info("Superuser updated with latest credentials")

        # 2. Create Categories
        logger.info("Creating initial categories...")
        categories = ["Electronics", "Clothing", "Home & Garden", "Books"]
        
        for cat_name in categories:
            result = await db.execute(select(Category).filter(Category.name == cat_name))
            cat = result.scalars().first()
            if not cat:
                cat = Category(name=cat_name, slug=cat_name.lower().replace(" ", "-"))
                db.add(cat)
        
        await db.commit()
        logger.info("Categories created")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_initial_data())
