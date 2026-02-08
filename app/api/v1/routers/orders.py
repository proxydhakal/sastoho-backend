from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies.auth import get_current_user, get_current_admin_user
from app.api.v1.routers.site_config import get_or_create_site_config
from app.core.database import get_db
from app.core.email import send_order_confirmed_email, send_order_status_email, send_order_completed_email
from app.models.user import User
from app.schemas.order import Order, OrderAdmin, OrderCreate, OrderUpdate
from app.services.order_service import order_service

router = APIRouter()

def _order_to_admin(order) -> OrderAdmin:
    data = Order.model_validate(order).model_dump()
    user = getattr(order, "user", None)
    data["customer_name"] = getattr(user, "full_name", None) if user else None
    data["customer_email"] = getattr(user, "email", None) if user else None
    return OrderAdmin(**data)


@router.get("/admin/all", response_model=List[OrderAdmin])
async def read_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    date_from: str = None,
    date_to: str = None,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Admin: Retrieve all orders. Filter by status, date range (ISO date strings), or search by order number/ID.
    """
    orders = await order_service.get_all_orders(
        db, skip=skip, limit=limit, status=status, date_from=date_from, date_to=date_to, search=search
    )
    return [_order_to_admin(o) for o in orders]


@router.get("/admin/{order_id}", response_model=OrderAdmin)
async def read_order_admin(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Admin: Get order details by ID (with items and product info).
    """
    order = await order_service.get_order_admin(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_admin(order)


@router.delete("/admin/{order_id}")
async def delete_order_admin(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Admin: Delete an order.
    """
    deleted = await order_service.delete_order(db, order_id=order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"msg": "Order deleted successfully"}


@router.patch("/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: int,
    status_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Admin: Update order status. Sends status-update email to customer; if status is 'completed', also sends order-completed email with item list.
    """
    order = await order_service.update_status(db, order_id=order_id, status=status_update.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Fetch full order with items and user for email and response
    order_full = await order_service.get_order_admin(db, order_id=order_id)
    if order_full and order_full.user:
        try:
            site_config = await get_or_create_site_config(db)
            logo_url = getattr(site_config, "logo_url", None)
            site_title = getattr(site_config, "site_title", None) or "SastoHo"
            email_to = order_full.user.email
            name = getattr(order_full.user, "full_name", None) or "Customer"
            order_number = (order_full.order_number or str(order_full.id).zfill(8))
            await send_order_status_email(
                email_to=email_to,
                recipient_name=name,
                order_number=order_number,
                new_status=status_update.status,
                logo_url=logo_url,
                site_title=site_title,
            )
            if status_update.status.lower() in ("completed", "delivered"):
                total_str = f"Rs. {float(order_full.total_amount):,.2f}"
                await send_order_completed_email(
                    email_to=email_to,
                    recipient_name=name,
                    order_number=order_number,
                    total_amount=total_str,
                    order_items=order_full.items,
                    logo_url=logo_url,
                    site_title=site_title,
                )
        except Exception as e:
            # Log but do not fail the status update
            import logging
            logging.getLogger(__name__).exception("Failed to send order status email: %s", e)
    return order_full if order_full else order

@router.post("/", response_model=Order)
async def create_order(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create new order from current cart. Sends order-confirmation email to customer.
    """
    try:
        order = await order_service.create_order(db, user_id=current_user.id, order_in=order_in)
        try:
            site_config = await get_or_create_site_config(db)
            logo_url = getattr(site_config, "logo_url", None)
            site_title = getattr(site_config, "site_title", None) or "SastoHo"
            total_str = f"Rs. {float(order.total_amount):,.2f}"
            order_number = (order.order_number or str(order.id).zfill(8))
            await send_order_confirmed_email(
                email_to=current_user.email,
                recipient_name=current_user.full_name,
                order_number=order_number,
                total_amount=total_str,
                status=order.status,
                logo_url=logo_url,
                site_title=site_title,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Failed to send order confirmation email: %s", e)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[Order])
async def read_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieve user orders.
    """
    orders = await order_service.get_orders(db, user_id=current_user.id)
    return orders

@router.get("/{order_id}", response_model=Order)
async def read_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get order by ID.
    """
    order = await order_service.get_order(db, order_id=order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
