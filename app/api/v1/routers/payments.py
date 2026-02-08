from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.services.payment_service import payment_service
from app.models.order import Order

router = APIRouter()

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe Webhooks.
    """
    payload = await request.body()
    
    try:
        event = payment_service.construct_event(payload, stripe_signature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle specific events
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        stripe_payment_id = payment_intent["id"]
        
        # Update Order Status
        stmt = select(Order).filter(Order.stripe_payment_id == stripe_payment_id)
        result = await db.execute(stmt)
        order = result.scalars().first()
        
        if order:
            order.status = "paid"
            await db.commit()
            # Can also trigger email here
    
    return {"status": "success"}
