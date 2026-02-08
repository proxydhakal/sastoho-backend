#!/usr/bin/env python3
"""
Script to create or update a superuser account with admin permissions.

Usage:
    python scripts/create_superuser.py
    python -m scripts.create_superuser
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
# Import all related models to ensure SQLAlchemy can resolve relationships
from app.models.cart import Cart
from app.models.wishlist import Wishlist
from app.models.order import Order
from app.models.review import Review
from app.models.product import Category, Product, ProductVariant, ProductImage
from app.models.user_group import UserGroup
from app.models.permission import Permission
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Superuser credentials
SUPERUSER_EMAIL = "proxydhakal@gmail.com"
SUPERUSER_PASSWORD = "SpringWinter!"
SUPERUSER_NAME = "Proxy Dhakal"


async def create_superuser():
    """Create or update superuser account with admin permissions."""
    async with SessionLocal() as db:
        try:
            # Check if user already exists
            logger.info(f"Checking if user '{SUPERUSER_EMAIL}' exists...")
            result = await db.execute(
                select(User)
                .filter(User.email == SUPERUSER_EMAIL)
                .options(selectinload(User.groups))
            )
            user = result.scalars().first()
            
            # Ensure admin group exists with all permissions
            logger.info("Checking for admin group...")
            admin_group_result = await db.execute(
                select(UserGroup)
                .filter(UserGroup.name == "Administrators")
                .options(selectinload(UserGroup.permissions))
            )
            admin_group = admin_group_result.scalars().first()
            
            if not admin_group:
                logger.info("Creating 'Administrators' group...")
                # Get all permissions
                permissions_result = await db.execute(select(Permission))
                all_permissions = permissions_result.scalars().all()
                
                admin_group = UserGroup(
                    name="Administrators",
                    description="Full administrative access to all features"
                )
                if all_permissions:
                    admin_group.permissions = list(all_permissions)
                db.add(admin_group)
                await db.flush()
                logger.info(f"✅ Created 'Administrators' group with {len(all_permissions)} permissions")
            else:
                # Ensure admin group has all permissions
                permissions_result = await db.execute(select(Permission))
                all_permissions = permissions_result.scalars().all()
                existing_permission_ids = {p.id for p in admin_group.permissions}
                new_permissions = [p for p in all_permissions if p.id not in existing_permission_ids]
                if new_permissions:
                    admin_group.permissions.extend(new_permissions)
                    await db.flush()
                    logger.info(f"✅ Updated 'Administrators' group with {len(new_permissions)} additional permissions")
            
            if user:
                # Update existing user
                logger.info(f"User '{SUPERUSER_EMAIL}' already exists. Updating to superuser...")
                user.hashed_password = get_password_hash(SUPERUSER_PASSWORD)
                user.is_superuser = True
                user.is_active = True
                user.is_verified = True
                user.role = "admin"
                if not user.full_name:
                    user.full_name = SUPERUSER_NAME
                
                # Assign to admin group if not already assigned
                if admin_group not in user.groups:
                    user.groups.append(admin_group)
                    logger.info("✅ Assigned user to 'Administrators' group")
                
                db.add(user)
                await db.commit()
                await db.refresh(user, ['groups'])
                logger.info(f"✅ Superuser '{SUPERUSER_EMAIL}' updated successfully!")
                logger.info(f"   - Email: {user.email}")
                logger.info(f"   - Name: {user.full_name}")
                logger.info(f"   - Role: {user.role}")
                logger.info(f"   - Is Superuser: {user.is_superuser}")
                logger.info(f"   - Is Active: {user.is_active}")
                logger.info(f"   - Is Verified: {user.is_verified}")
                logger.info(f"   - Groups: {[g.name for g in user.groups]}")
            else:
                # Create new superuser
                logger.info(f"Creating new superuser '{SUPERUSER_EMAIL}'...")
                user = User(
                    email=SUPERUSER_EMAIL,
                    hashed_password=get_password_hash(SUPERUSER_PASSWORD),
                    full_name=SUPERUSER_NAME,
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                    role="admin"
                )
                # Assign to admin group
                user.groups = [admin_group]
                db.add(user)
                await db.commit()
                await db.refresh(user, ['groups'])
                logger.info(f"✅ Superuser '{SUPERUSER_EMAIL}' created successfully!")
                logger.info(f"   - Email: {user.email}")
                logger.info(f"   - Name: {user.full_name}")
                logger.info(f"   - Role: {user.role}")
                logger.info(f"   - Is Superuser: {user.is_superuser}")
                logger.info(f"   - Is Active: {user.is_active}")
                logger.info(f"   - Is Verified: {user.is_verified}")
                logger.info(f"   - Groups: {[g.name for g in user.groups]}")
            
            logger.info("\n🎉 Superuser setup complete!")
            logger.info(f"   You can now login with:")
            logger.info(f"   Email: {SUPERUSER_EMAIL}")
            logger.info(f"   Password: {SUPERUSER_PASSWORD}")
            logger.info(f"\n   Admin panel access: ✅ Enabled")
            logger.info(f"   User has been assigned to 'Administrators' group with all permissions")
            
        except Exception as e:
            logger.error(f"❌ Error creating superuser: {e}", exc_info=True)
            await db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Creating Superuser Account with Admin Permissions")
    logger.info("=" * 60)
    asyncio.run(create_superuser())
