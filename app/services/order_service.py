import random
import string
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem

# 8-char alphanumeric (uppercase + digits) for order_number
ORDER_NUMBER_CHARS = string.ascii_uppercase + string.digits
ORDER_NUMBER_LENGTH = 8


def _generate_order_number() -> str:
    return "".join(random.choices(ORDER_NUMBER_CHARS, k=ORDER_NUMBER_LENGTH))
from app.models.cart import Cart, CartItem
from app.models.product import ProductVariant
from app.models.address import Address
from app.models.user import User
from app.schemas.order import OrderCreate
from app.services.promo_service import promo_code_service

class OrderService:
    async def create_order(self, db: AsyncSession, user_id: int, order_in: OrderCreate) -> Order:
        # 1. Get User Cart
        stmt = select(Cart).filter(Cart.user_id == user_id).options(
            selectinload(Cart.items).selectinload(CartItem.variant)
        )
        result = await db.execute(stmt)
        cart = result.scalars().first()
        
        if not cart or not cart.items:
            raise ValueError("Cart is empty")

        # 3. Calculate Total & Create Items
        total_amount = Decimal("0.00")
        order_items = []
        
        for item in cart.items:
            # Check stock
            if item.variant.stock_quantity < item.quantity:
                raise ValueError(f"Insufficient stock for {item.variant.sku}")
            
            item_total = item.variant.price * item.quantity
            total_amount += item_total
            
            order_item = OrderItem(
                product_variant_id=item.variant.id,
                quantity=item.quantity,
                price_at_purchase=item.variant.price
            )
            order_items.append(order_item)
            
            # Deduct stock (simple version, ideally reserve)
            item.variant.stock_quantity -= item.quantity

        # Apply promo code if provided (validate server-side)
        discount_amount = Decimal("0.00")
        promo_code_id = None
        if order_in.promo_code and order_in.promo_code.strip():
            try:
                validation = await promo_code_service.validate_promo_code(
                    db, code=order_in.promo_code.strip(), total_amount=total_amount, user_id=user_id
                )
                if validation.valid and validation.discount_amount is not None:
                    discount_amount = validation.discount_amount
                    if validation.promo_code:
                        promo_code_id = validation.promo_code.id
                # If invalid, we proceed without discount (no error, ignore bad code)
            except Exception as e:
                # Log promo code validation error but don't fail the order
                import logging
                logging.getLogger(__name__).warning(f"Promo code validation error: {e}. Proceeding without discount.")
                discount_amount = Decimal("0.00")
                promo_code_id = None

        final_amount = total_amount - discount_amount
        if final_amount < 0:
            final_amount = Decimal("0.00")

        # 4. Payment: COD skips Stripe; other methods use Stripe (or future Esewa/Khalti)
        payment_method = (order_in.payment_method or "cod").lower().strip()
        stripe_payment_id = None
        if payment_method not in ("cod", "esewa", "khalti"):
            from app.services.payment_service import payment_service
            amount_cents = int(final_amount * 100)
            payment_intent = payment_service.create_payment_intent(
                amount=amount_cents,
                metadata={"user_id": str(user_id)}
            )
            stripe_payment_id = payment_intent.id

        # 5. Get shipping address data
        shipping_address_data = order_in.shipping_address
        if order_in.shipping_address_id:
            stmt_addr = select(Address).filter(Address.id == order_in.shipping_address_id)
            result_addr = await db.execute(stmt_addr)
            address = result_addr.scalars().first()
            if not address:
                raise ValueError(f"Shipping address with ID {order_in.shipping_address_id} not found")
            if address.user_id != user_id:
                raise ValueError("Shipping address does not belong to the current user")
            shipping_address_data = {
                "full_name": address.full_name,
                "phone_number": address.phone_number,
                "street": address.street,
                "city": address.city,
                "state": address.state,
                "postal_code": address.postal_code,
                "country": address.country,
            }
        if not shipping_address_data:
            raise ValueError("Shipping address is required. Provide either shipping_address or shipping_address_id")

        # 6. Generate unique order number BEFORE creating the order
        order_number = None
        for _ in range(20):  # Try up to 20 times to find a unique order number
            code = _generate_order_number()
            existing = await db.execute(select(Order).where(Order.order_number == code))
            if existing.scalar_one_or_none() is None:
                order_number = code
                break
        if not order_number:
            raise ValueError("Could not generate unique order number after multiple attempts")

        # 7. Create Order with order_number
        order = Order(
            user_id=user_id,
            order_number=order_number,
            status="pending",
            total_amount=final_amount,
            shipping_address=shipping_address_data,
            shipping_address_id=order_in.shipping_address_id,
            billing_address_id=order_in.billing_address_id,
            stripe_payment_id=stripe_payment_id,
            payment_method=payment_method,
            promo_code_id=promo_code_id,
            discount_amount=discount_amount if discount_amount > 0 else None,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

        # 4. Attach Items
        for item in order_items:
            item.order_id = order.id
            db.add(item)
        
        # 5. Clear Cart items (but keep cart?)
        for item in cart.items:
            await db.delete(item)

        # 5b. Record promo usage if applied
        if promo_code_id is not None and discount_amount > 0:
            await promo_code_service.apply_promo_code(
                db, promo_code_id=promo_code_id, order_id=order.id,
                discount_amount=discount_amount, user_id=user_id
            )
            
        await db.commit()
        await db.refresh(order)
        
        # Re-fetch with items and variant.product for schema
        stmt = select(Order).filter(Order.id == order.id).options(
            selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    def _order_load_options(self):
        return selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product)

    async def get_orders(self, db: AsyncSession, user_id: int) -> List[Order]:
        stmt = select(Order).filter(Order.user_id == user_id).options(self._order_load_options())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_order(self, db: AsyncSession, order_id: int, user_id: int) -> Optional[Order]:
        stmt = select(Order).filter(Order.id == order_id, Order.user_id == user_id).options(self._order_load_options())
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_order_admin(self, db: AsyncSession, order_id: int) -> Optional[Order]:
        stmt = select(Order).filter(Order.id == order_id).options(
            self._order_load_options(),
            selectinload(Order.user),
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_all_orders(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Order]:
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import or_, cast, String
        stmt = select(Order).options(
            self._order_load_options(),
            selectinload(Order.user),
        )
        if status and status.strip():
            stmt = stmt.filter(Order.status == status.strip())
        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.filter(
                or_(
                    Order.order_number.ilike(term),
                    cast(Order.id, String).ilike(term),
                )
            )
        if date_from:
            try:
                dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                stmt = stmt.filter(Order.created_at >= dt)
            except (ValueError, TypeError):
                pass
        if date_to:
            try:
                dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt = dt + timedelta(days=1)
                stmt = stmt.filter(Order.created_at < dt)
            except (ValueError, TypeError):
                pass
        stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def delete_order(self, db: AsyncSession, order_id: int) -> bool:
        result = await db.execute(select(Order).filter(Order.id == order_id))
        order = result.scalars().first()
        if not order:
            return False
        await db.delete(order)
        await db.commit()
        return True

    async def update_status(self, db: AsyncSession, order_id: int, status: str) -> Optional[Order]:
        stmt = select(Order).filter(Order.id == order_id)
        result = await db.execute(stmt)
        order = result.scalars().first()
        if order:
            order.status = status
            db.add(order)
            await db.commit()
            await db.refresh(order)
        return order

order_service = OrderService()
