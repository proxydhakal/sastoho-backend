from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.api.v1.dependencies.auth import get_current_active_user
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.order import Order
from app.models.review import Review
from app.models.user_group import UserGroup
from app.models.permission import Permission
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.schemas.user_group import (
    UserGroup as UserGroupSchema,
    UserGroupCreate,
    UserGroupUpdate,
    Permission as PermissionSchema,
    PermissionCreate
)
from app.schemas.review import ReviewOut
from app.models.product import Product

router = APIRouter()

# Dependency to check admin role
def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get global statistics (Users, Orders, Revenue).
    """
    # Count Users
    user_count_res = await db.execute(select(func.count(User.id)))
    user_count = user_count_res.scalar()

    # Count Orders
    order_count_res = await db.execute(select(func.count(Order.id)))
    order_count = order_count_res.scalar()

    # Total Revenue (Sum of paid/completed/delivered orders)
    revenue_res = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0)).filter(
            Order.status.in_(["paid", "completed", "delivered", "shipped"])
        )
    )
    total_revenue = float(revenue_res.scalar() or 0)

    return {
        "total_users": user_count,
        "total_orders": order_count,
        "total_revenue": total_revenue
    }


@router.get("/stats/charts")
async def get_admin_stats_charts(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get chart data: orders per day and revenue per day for the last `days` days.
    """
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import cast, Date

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=max(1, min(days, 90)))

    # Orders per day
    order_date = cast(Order.created_at, Date)
    orders_by_day_stmt = (
        select(order_date.label("date"), func.count(Order.id).label("count"))
        .filter(order_date >= start_date, order_date <= end_date)
        .group_by(order_date)
        .order_by(order_date)
    )
    orders_result = await db.execute(orders_by_day_stmt)
    orders_rows = orders_result.all()

    # Revenue per day (paid/completed/delivered/shipped)
    revenue_by_day_stmt = (
        select(order_date.label("date"), func.coalesce(func.sum(Order.total_amount), 0).label("total"))
        .filter(
            order_date >= start_date,
            order_date <= end_date,
            Order.status.in_(["paid", "completed", "delivered", "shipped"]),
        )
        .group_by(order_date)
        .order_by(order_date)
    )
    revenue_result = await db.execute(revenue_by_day_stmt)
    revenue_rows = revenue_result.all()

    # Fill missing days with 0
    by_date_orders = {str(r.date): r.count for r in orders_rows}
    by_date_revenue = {str(r.date): float(r.total) for r in revenue_rows}
    orders_by_day = []
    revenue_by_day = []
    d = start_date
    while d <= end_date:
        key = str(d)
        orders_by_day.append({"date": key, "count": by_date_orders.get(key, 0)})
        revenue_by_day.append({"date": key, "total": by_date_revenue.get(key, 0)})
        d += timedelta(days=1)

    return {
        "orders_by_day": orders_by_day,
        "revenue_by_day": revenue_by_day,
    }

@router.get("/users", response_model=List[UserSchema])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all users (admin only). Optional search by email or full_name.
    """
    from sqlalchemy import or_
    stmt = select(User).options(selectinload(User.groups))
    if search and search.strip():
        q = f"%{search.strip()}%"
        stmt = stmt.filter(or_(User.email.ilike(q), User.full_name.ilike(q)))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users

@router.post("/users", response_model=UserSchema)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new user (admin only).
    """
    # Check if user already exists
    existing_user = await db.execute(select(User).filter(User.email == user_in.email))
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=user_in.is_active if user_in.is_active is not None else True,
        role="customer"
    )
    db.add(user)
    await db.flush()
    
    # Assign groups if provided
    if user_in.group_ids:
        groups = await db.execute(select(UserGroup).filter(UserGroup.id.in_(user_in.group_ids)))
        user.groups = groups.scalars().all()
    
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get a specific user (admin only).
    """
    stmt = select(User).filter(User.id == user_id).options(selectinload(User.groups))
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update a user (admin only).
    """
    stmt = select(User).filter(User.id == user_id).options(selectinload(User.groups))
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    update_data = user_in.model_dump(exclude_unset=True, exclude={"password", "group_ids"})
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Update password if provided
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    
    # Update groups if provided
    if user_in.group_ids is not None:
        groups = await db.execute(select(UserGroup).filter(UserGroup.id.in_(user_in.group_ids)))
        user.groups = groups.scalars().all()
    
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a user (admin only).
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return {"status": "success", "message": "User deleted successfully"}

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    is_superuser: bool = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Promote/Demote a user.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_superuser = is_superuser
    if is_superuser:
        user.role = "admin"
    else:
        user.role = "customer"

    await db.commit()
    return {"status": "success", "role": user.role}

# User Groups Endpoints
@router.get("/groups", response_model=List[UserGroupSchema])
async def get_all_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all user groups.
    """
    stmt = select(UserGroup).options(selectinload(UserGroup.permissions))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/groups", response_model=UserGroupSchema)
async def create_group(
    group_in: UserGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new user group.
    """
    # Check if group already exists
    existing = await db.execute(select(UserGroup).filter(UserGroup.name == group_in.name))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Group with this name already exists")
    
    group = UserGroup(
        name=group_in.name,
        description=group_in.description
    )
    db.add(group)
    await db.flush()
    
    # Assign permissions if provided
    if group_in.permission_ids:
        permissions = await db.execute(select(Permission).filter(Permission.id.in_(group_in.permission_ids)))
        group.permissions = permissions.scalars().all()
    
    await db.commit()
    await db.refresh(group)
    return group

@router.get("/groups/{group_id}", response_model=UserGroupSchema)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get a specific user group.
    """
    stmt = select(UserGroup).filter(UserGroup.id == group_id).options(selectinload(UserGroup.permissions))
    result = await db.execute(stmt)
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.patch("/groups/{group_id}", response_model=UserGroupSchema)
async def update_group(
    group_id: int,
    group_in: UserGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update a user group.
    """
    stmt = select(UserGroup).filter(UserGroup.id == group_id).options(selectinload(UserGroup.permissions))
    result = await db.execute(stmt)
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    update_data = group_in.model_dump(exclude_unset=True, exclude={"permission_ids"})
    for field, value in update_data.items():
        setattr(group, field, value)
    
    # Update permissions if provided
    if group_in.permission_ids is not None:
        permissions = await db.execute(select(Permission).filter(Permission.id.in_(group_in.permission_ids)))
        group.permissions = permissions.scalars().all()
    
    await db.commit()
    await db.refresh(group)
    return group

@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a user group.
    """
    group = await db.get(UserGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    await db.delete(group)
    await db.commit()
    return {"status": "success", "message": "Group deleted successfully"}

# Permissions Endpoints
@router.get("/permissions", response_model=List[PermissionSchema])
async def get_all_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all permissions.
    """
    result = await db.execute(select(Permission))
    return result.scalars().all()

@router.post("/permissions", response_model=PermissionSchema)
async def create_permission(
    permission_in: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new permission.
    """
    # Check if permission already exists
    existing = await db.execute(select(Permission).filter(Permission.codename == permission_in.codename))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Permission with this codename already exists")
    
    permission = Permission(
        name=permission_in.name,
        codename=permission_in.codename,
        description=permission_in.description
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission

@router.delete("/permissions/{permission_id}")
async def delete_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a permission.
    """
    permission = await db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    await db.delete(permission)
    await db.commit()
    return {"status": "success", "message": "Permission deleted successfully"}

# Reviews Management Endpoints
@router.get("/reviews", response_model=List[ReviewOut])
async def get_all_reviews(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all reviews (admin only). Optional search by comment, product name, or user email/name.
    """
    from sqlalchemy import or_
    stmt = select(Review).options(
        selectinload(Review.user),
        selectinload(Review.product)
    )
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.join(Review.product).join(Review.user).filter(
            or_(
                Review.comment.ilike(term),
                Product.name.ilike(term),
                User.email.ilike(term),
                User.full_name.ilike(term),
            )
        )
    stmt = stmt.offset(skip).limit(limit).order_by(Review.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a review (admin only).
    """
    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    await db.delete(review)
    await db.commit()
    return {"status": "success", "message": "Review deleted successfully"}

@router.patch("/reviews/{review_id}/approve")
async def approve_review(
    review_id: int,
    is_approved: bool = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Approve or reject a review (admin only).
    """
    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.is_approved = is_approved
    await db.commit()
    await db.refresh(review)
    
    # Load relationships for response
    stmt = select(Review).filter(Review.id == review.id).options(
        selectinload(Review.user),
        selectinload(Review.product)
    )
    result = await db.execute(stmt)
    return result.scalars().first()
