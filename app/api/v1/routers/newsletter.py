"""Newsletter subscription - public endpoint."""
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core import email as email_utils
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.api.v1.routers.site_config import get_or_create_site_config

router = APIRouter()


class NewsletterSubscribe(BaseModel):
    email: EmailStr


@router.post("/subscribe", response_model=dict)
async def subscribe_newsletter(
    data: NewsletterSubscribe = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Subscribe to newsletter. Sends confirmation email.
    """
    email = data.email

    result = await db.execute(select(NewsletterSubscriber).filter(NewsletterSubscriber.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        return {"msg": "You are already subscribed to our newsletter."}

    subscriber = NewsletterSubscriber(email=email)
    db.add(subscriber)
    await db.commit()

    site_config = await get_or_create_site_config(db)
    await email_utils.send_newsletter_welcome_email(
        email_to=email,
        logo_url=site_config.logo_url,
        site_title=site_config.site_title or "SastoHo",
        contact_email=site_config.contact_email,
    )
    return {"msg": "Thank you for subscribing! Check your email for confirmation."}
