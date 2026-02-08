"""Email sending using HTML templates with logo and site colors."""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from app.core.email_templates import (
    verification_email_html,
    password_reset_email_html,
    newsletter_welcome_email_html,
    contact_thankyou_email_html,
    contact_admin_notify_email_html,
    order_confirmed_email_html,
    order_status_update_email_html,
    order_completed_email_html,
)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.EMAIL_HOST_USER,
    MAIL_PASSWORD=settings.EMAIL_HOST_PASSWORD,
    MAIL_FROM=settings.FROM_EMAIL,
    MAIL_PORT=settings.EMAIL_PORT,
    MAIL_SERVER=settings.EMAIL_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fastmail = FastMail(conf)


DEFAULT_LOGO_PATH = "static/logo/logo.png"
SUPPORT_EMAIL = "support@sastoho.com"


def _logo_url(relative_path: str | None) -> str | None:
    """Build full logo URL for emails. Uses static/logo/logo.png when not provided."""
    path = (relative_path or DEFAULT_LOGO_PATH).strip()
    if not path:
        return None
    base = settings.API_URL.rstrip("/")
    path = path.lstrip("/").replace("\\", "/")
    return f"{base}/{path}"


async def send_verification_email(
    email_to: str,
    token: str,
    full_name: str | None = None,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> None:
    """Send email verification link after signup."""
    verify_link = f"{settings.FRONTEND_URL.rstrip('/')}/auth/verify-email?token={token}"
    html = verification_email_html(
        recipient_name=full_name or "Customer",
        verify_link=verify_link,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_reset_password_email(
    email_to: str,
    token: str,
    full_name: str | None = None,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> None:
    """Send password reset link."""
    reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/auth/reset-password?token={token}"
    html = password_reset_email_html(
        recipient_name=full_name or "Customer",
        reset_link=reset_link,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_newsletter_welcome_email(
    email_to: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
    contact_email: str | None = None,
) -> None:
    """Send newsletter subscription confirmation."""
    html = newsletter_welcome_email_html(
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        contact_email=contact_email or SUPPORT_EMAIL,
    )
    message = MessageSchema(
        subject=f"Welcome to {site_title} Newsletter",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_contact_thankyou_email(
    email_to: str,
    name: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
    contact_email: str | None = None,
) -> None:
    """Send thank-you email after contact form submission."""
    html = contact_thankyou_email_html(
        recipient_name=name,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        contact_email=contact_email or SUPPORT_EMAIL,
    )
    message = MessageSchema(
        subject=f"We Received Your Message - {site_title}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_contact_admin_notify_email(
    admin_email: str,
    name: str,
    email: str,
    subject: str,
    message: str,
    submission_type: str = "feedback",
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> None:
    """Notify admin when contact form is submitted."""
    html = contact_admin_notify_email_html(
        name=name,
        email=email,
        subject=subject,
        message=message,
        submission_type=submission_type,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    msg = MessageSchema(
        subject=f"[{site_title}] New Contact Form: {subject[:50]}",
        recipients=[admin_email],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(msg)


def _orders_url() -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/orders"


async def send_order_confirmed_email(
    email_to: str,
    recipient_name: str | None,
    order_number: str,
    total_amount: str,
    status: str = "pending",
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> None:
    """Send order confirmation email after order is placed. order_number: 8-digit tracking ID."""
    html = order_confirmed_email_html(
        recipient_name=recipient_name or "Customer",
        order_number=order_number,
        total_amount=total_amount,
        status=status,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        orders_url=_orders_url(),
    )
    message = MessageSchema(
        subject=f"Order Confirmed #{order_number} - {site_title}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_order_status_email(
    email_to: str,
    recipient_name: str | None,
    order_number: str,
    new_status: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> None:
    """Send email when order status is updated. order_number: 8-digit tracking ID."""
    html = order_status_update_email_html(
        recipient_name=recipient_name or "Customer",
        order_number=order_number,
        new_status=new_status,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        orders_url=_orders_url(),
    )
    message = MessageSchema(
        subject=f"Order #{order_number} - Status: {new_status} - {site_title}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_order_completed_email(
    email_to: str,
    recipient_name: str | None,
    order_number: str,
    total_amount: str,
    order_items: list,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> None:
    """Send order completed email with list of order items. order_number: 8-digit tracking ID. order_items: list of objects with variant (with product.name), quantity, price_at_purchase."""
    rows = []
    for item in order_items:
        name = "Product"
        if getattr(item, "variant", None) and getattr(item.variant, "product", None):
            name = item.variant.product.name or name
        elif getattr(item, "variant", None):
            name = getattr(item.variant, "sku", name)
        qty = getattr(item, "quantity", 0)
        price = getattr(item, "price_at_purchase", 0)
        try:
            line_total = float(price) * int(qty)
        except (TypeError, ValueError):
            line_total = 0
        rows.append(
            f'<tr><td style="padding:10px;border:1px solid #d1d5db;">{name}</td>'
            f'<td style="text-align:center;padding:10px;border:1px solid #d1d5db;">{qty}</td>'
            f'<td style="text-align:right;padding:10px;border:1px solid #d1d5db;">Rs. {line_total:,.2f}</td></tr>'
        )
    items_html = "\n".join(rows)
    html = order_completed_email_html(
        recipient_name=recipient_name or "Customer",
        order_number=order_number,
        total_amount=total_amount,
        items_html=items_html,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        orders_url=_orders_url(),
    )
    message = MessageSchema(
        subject=f"Order Completed #{order_number} - {site_title}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)
