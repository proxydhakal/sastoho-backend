from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.promo import PromoCode, PromoCodeUsage
from app.schemas.promo import PromoCodeCreate, PromoCodeUpdate, PromoCodeValidationResult
from app.crud.base import CRUDBase


class CRUDPromoCode(CRUDBase[PromoCode, PromoCodeCreate, PromoCodeUpdate]):
    async def validate_promo_code(
        self, 
        db: AsyncSession, 
        code: str, 
        total_amount: Decimal,
        user_id: Optional[int] = None
    ) -> PromoCodeValidationResult:
        """Validate a promo code and calculate discount."""
        now = datetime.now(timezone.utc)
        
        # Use is_(True) for MySQL compatibility (SQLAlchemy handles boolean conversion)
        stmt = select(PromoCode).filter(
            PromoCode.code == code.upper().strip(),
            PromoCode.is_active.is_(True),
            PromoCode.valid_from <= now,
            PromoCode.valid_until >= now
        )
        result = await db.execute(stmt)
        promo_code = result.scalars().first()
        
        if not promo_code:
            return PromoCodeValidationResult(
                valid=False,
                message="Promo code not found or expired"
            )
        
        # Check usage limit
        if promo_code.usage_limit and promo_code.used_count >= promo_code.usage_limit:
            return PromoCodeValidationResult(
                valid=False,
                message="Promo code usage limit reached"
            )
        
        # Check minimum purchase amount
        if promo_code.min_purchase_amount and total_amount < promo_code.min_purchase_amount:
            return PromoCodeValidationResult(
                valid=False,
                message=f"Minimum purchase amount of {promo_code.min_purchase_amount} required"
            )
        
        # Calculate discount
        if promo_code.discount_type == "percentage":
            discount_amount = (total_amount * promo_code.discount_value) / 100
            if promo_code.max_discount_amount:
                discount_amount = min(discount_amount, promo_code.max_discount_amount)
        else:  # fixed
            discount_amount = promo_code.discount_value
        
        # Ensure discount doesn't exceed total amount
        discount_amount = min(discount_amount, total_amount)
        
        return PromoCodeValidationResult(
            valid=True,
            discount_amount=discount_amount,
            promo_code=promo_code,
            message="Promo code applied successfully"
        )
    
    async def apply_promo_code(
        self,
        db: AsyncSession,
        promo_code_id: int,
        order_id: int,
        discount_amount: Decimal,
        user_id: Optional[int] = None
    ) -> PromoCodeUsage:
        """Record promo code usage."""
        promo_code = await self.get(db, id=promo_code_id)
        if promo_code:
            promo_code.used_count += 1
            db.add(promo_code)
        
        usage = PromoCodeUsage(
            promo_code_id=promo_code_id,
            user_id=user_id,
            order_id=order_id,
            discount_amount=discount_amount,
            used_at=datetime.now(timezone.utc)
        )
        db.add(usage)
        await db.commit()
        await db.refresh(usage)
        return usage


promo_code_service = CRUDPromoCode(PromoCode)
