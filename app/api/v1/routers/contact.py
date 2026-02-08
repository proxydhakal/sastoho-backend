from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core import email as email_utils
from app.api.v1.dependencies.auth import get_current_user_optional
from app.api.v1.routers.site_config import get_or_create_site_config
from app.models.user import User
from app.models.contact_submission import ContactSubmission
from app.schemas.contact import ContactSubmissionCreate, ContactSubmissionOut

router = APIRouter()


@router.post("/", response_model=ContactSubmissionOut, status_code=201)
async def submit_contact(
    data: ContactSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Submit contact form (feedback or grievance). Sends thank-you email to user and notifies admin."""
    submission = ContactSubmission(
        name=data.name,
        email=data.email,
        subject=data.subject,
        message=data.message,
        submission_type=data.submission_type,
        user_id=current_user.id if current_user else None,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    site_config = await get_or_create_site_config(db)
    logo_url = site_config.logo_url
    site_title = site_config.site_title or "SastoHo"
    contact_email = site_config.contact_email

    await email_utils.send_contact_thankyou_email(
        email_to=data.email,
        name=data.name,
        logo_url=logo_url,
        site_title=site_title,
        contact_email=contact_email,
    )
    if contact_email:
        await email_utils.send_contact_admin_notify_email(
            admin_email=contact_email,
            name=data.name,
            email=data.email,
            subject=data.subject,
            message=data.message,
            submission_type=data.submission_type,
            logo_url=logo_url,
            site_title=site_title,
        )
    return submission
