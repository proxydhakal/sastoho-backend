from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core import security

class UserService:
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()
    
    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        hashed_password = security.get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role="customer", # Default role
            is_active=True,
            is_verified=False 
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(db, email)
        if not user:
            return None
        if not security.verify_password(password, user.hashed_password):
            return None
        return user

user_service = UserService()
