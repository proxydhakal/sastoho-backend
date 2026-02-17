"""HTML email templates with site logo and colors (#317791 teal, #a8cc45 lime)."""

# Site colors (from website template)
PRIMARY_COLOR = "#317791"  # teal
ACCENT_COLOR = "#a8cc45"   # lime green
TEXT_COLOR = "#374151"
LIGHT_BG = "#f3f4f6"


def _base_html(title: str, body_content: str, logo_url: str | None, site_title: str = "SastoHo") -> str:
    """Base HTML wrapper with header (logo), body, footer."""
    logo_section = ""
    if logo_url:
        logo_section = f'<img src="{logo_url}" alt="{site_title}" style="max-height:48px;max-width:180px;height:auto;" />'
    else:
        logo_section = f'<span style="font-size:24px;font-weight:800;color:white;">{site_title}</span>'

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background-color:#f8fafc;color:{TEXT_COLOR};">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;margin:0 auto;background:#fff;">
    <tr>
      <td style="background:{PRIMARY_COLOR};padding:24px 32px;text-align:center;">
        {logo_section}
      </td>
    </tr>
    <tr>
      <td style="padding:32px;line-height:1.6;font-size:15px;">
        {body_content}
      </td>
    </tr>
    <tr>
      <td style="padding:24px 32px;background:{LIGHT_BG};font-size:12px;color:#6b7280;text-align:center;">
        &copy; 2026 {site_title}. All rights reserved.
      </td>
    </tr>
  </table>
</body>
</html>"""


def verification_email_html(
    recipient_name: str,
    verify_link: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> str:
    """Email verification after signup."""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Thank you for signing up! Please verify your email address by clicking the button below.</p>
    <div style="margin:24px 0;">
      <a href="{verify_link}" style="display:inline-block;background:{ACCENT_COLOR};color:#1f2937;padding:14px 28px;text-decoration:none;font-weight:bold;border-radius:12px;">Verify Email</a>
    </div>
    <p style="margin:0 0 16px;color:#6b7280;font-size:14px;">If you did not create an account, please ignore this email.</p>
    <p style="margin:0;">This link expires in 24 hours.</p>
    """
    return _base_html("Verify Your Email", body, logo_url, site_title)


def verification_otp_email_html(
    recipient_name: str,
    otp: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
    expire_minutes: int = 10,
) -> str:
    """Email verification OTP after signup."""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Thank you for signing up! Use the OTP below to verify your email address in the app.</p>
    <div style="margin:24px 0;padding:24px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:8px;text-align:center;">
      <p style="margin:0 0 8px;font-size:12px;color:#6b7280;letter-spacing:2px;">YOUR VERIFICATION CODE</p>
      <p style="margin:0;font-size:32px;font-weight:800;letter-spacing:8px;color:{PRIMARY_COLOR};">{otp}</p>
    </div>
    <p style="margin:0 0 16px;color:#6b7280;font-size:14px;">If you did not create an account, please ignore this email.</p>
    <p style="margin:0;">This code expires in {expire_minutes} minutes.</p>
    """
    return _base_html("Verify Your Email", body, logo_url, site_title)


def password_reset_email_html(
    recipient_name: str,
    reset_link: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> str:
    """Password reset request."""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">You requested a password reset. Click the button below to set a new password.</p>
    <div style="margin:24px 0;">
      <a href="{reset_link}" style="display:inline-block;background:{ACCENT_COLOR};color:#1f2937;padding:14px 28px;text-decoration:none;font-weight:bold;border-radius:12px;">Reset Password</a>
    </div>
    <p style="margin:0 0 16px;color:#6b7280;font-size:14px;">If you did not request this, please ignore this email. Your password will remain unchanged.</p>
    <p style="margin:0;">This link expires in 1 hour.</p>
    """
    return _base_html("Password Reset Request", body, logo_url, site_title)


def newsletter_welcome_email_html(
    logo_url: str | None = None,
    site_title: str = "SastoHo",
    contact_email: str | None = None,
) -> str:
    """Newsletter subscription confirmation."""
    contact_line = f'<p style="margin:0;">For queries, contact us at: <a href="mailto:{contact_email}" style="color:{PRIMARY_COLOR};text-decoration:underline;">{contact_email}</a></p>' if contact_email else ""
    body = f"""
    <p style="margin:0 0 16px;">Thank you for subscribing to our newsletter!</p>
    <p style="margin:0 0 16px;">You will receive exclusive deals, new arrivals, and updates straight to your inbox.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;font-weight:bold;">What to expect:</p>
      <ul style="margin:0;padding-left:20px;">
        <li>Early access to sales and promotions</li>
        <li>New product launches</li>
        <li>Helpful tips and guides</li>
      </ul>
    </div>
    {contact_line}
    """
    return _base_html("Welcome to Our Newsletter", body, logo_url, site_title)


def contact_thankyou_email_html(
    recipient_name: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
    contact_email: str | None = None,
) -> str:
    """Thank-you email after contact form submission."""
    contact_line = f'<p style="margin:0;">You can also reach us at: <a href="mailto:{contact_email}" style="color:{PRIMARY_COLOR};text-decoration:underline;">{contact_email}</a></p>' if contact_email else ""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name},</p>
    <p style="margin:0 0 16px;">Thank you for reaching out! We have received your message and will get back to you shortly.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0;font-weight:bold;">Our team typically responds within 24-48 hours.</p>
    </div>
    {contact_line}
    """
    return _base_html("We Received Your Message", body, logo_url, site_title)


def contact_admin_notify_email_html(
    name: str,
    email: str,
    subject: str,
    message: str,
    submission_type: str = "feedback",
    logo_url: str | None = None,
    site_title: str = "SastoHo",
) -> str:
    """Admin notification when contact form is submitted."""
    body = f"""
    <p style="margin:0 0 16px;">A new contact form submission has been received.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;"><strong>Name:</strong> {name}</p>
      <p style="margin:0 0 8px;"><strong>Email:</strong> <a href="mailto:{email}" style="color:{PRIMARY_COLOR};">{email}</a></p>
      <p style="margin:0 0 8px;"><strong>Subject:</strong> {subject}</p>
      <p style="margin:0 0 8px;"><strong>Type:</strong> {submission_type}</p>
      <p style="margin:16px 0 0;"><strong>Message:</strong></p>
      <p style="margin:8px 0 0;white-space:pre-wrap;">{message}</p>
    </div>
    """
    return _base_html("New Contact Form Submission", body, logo_url, site_title)


def order_confirmed_email_html(
    recipient_name: str,
    order_number: str,
    total_amount: str,
    status: str = "pending",
    logo_url: str | None = None,
    site_title: str = "SastoHo",
    orders_url: str | None = None,
) -> str:
    """Order confirmation email after order is placed. order_number: 8-digit tracking ID."""
    orders_link = f'<p style="margin:16px 0 0;"><a href="{orders_url}" style="color:{PRIMARY_COLOR};font-weight:bold;">View your orders</a></p>' if orders_url else ""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Thank you for your order! We have received it and will process it shortly.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;"><strong>Order ID:</strong> #{order_number}</p>
      <p style="margin:0 0 8px;"><strong>Status:</strong> {status}</p>
      <p style="margin:0 0 8px;"><strong>Total:</strong> {total_amount}</p>
    </div>
    {orders_link}
    """
    return _base_html("Order Confirmed", body, logo_url, site_title)


def order_status_update_email_html(
    recipient_name: str,
    order_number: str,
    new_status: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
    orders_url: str | None = None,
) -> str:
    """Email when order status is updated (any step). order_number: 8-digit tracking ID."""
    orders_link = f'<p style="margin:16px 0 0;"><a href="{orders_url}" style="color:{PRIMARY_COLOR};font-weight:bold;">View order details</a></p>' if orders_url else ""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Your order status has been updated.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;"><strong>Order ID:</strong> #{order_number}</p>
      <p style="margin:0 0 8px;"><strong>New status:</strong> {new_status}</p>
    </div>
    {orders_link}
    """
    return _base_html("Order Status Update", body, logo_url, site_title)


def order_completed_email_html(
    recipient_name: str,
    order_number: str,
    total_amount: str,
    items_html: str,
    logo_url: str | None = None,
    site_title: str = "SastoHo",
    orders_url: str | None = None,
) -> str:
    """Order completed email with list of order items. order_number: 8-digit tracking ID."""
    orders_link = f'<p style="margin:16px 0 0;"><a href="{orders_url}" style="color:{PRIMARY_COLOR};font-weight:bold;">View order details</a></p>' if orders_url else ""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Your order has been completed. Thank you for shopping with us!</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;"><strong>Order ID:</strong> #{order_number}</p>
      <p style="margin:0 0 8px;"><strong>Total:</strong> {total_amount}</p>
    </div>
    <p style="margin:16px 0 8px;"><strong>Order items:</strong></p>
    <table style="width:100%;border-collapse:collapse;font-size:14px;margin:0 0 16px;">
      <thead>
        <tr style="background:#e5e7eb;">
          <th style="text-align:left;padding:10px;border:1px solid #d1d5db;">Product</th>
          <th style="text-align:center;padding:10px;border:1px solid #d1d5db;">Qty</th>
          <th style="text-align:right;padding:10px;border:1px solid #d1d5db;">Price</th>
        </tr>
      </thead>
      <tbody>
        {items_html}
      </tbody>
    </table>
    {orders_link}
    """
    return _base_html("Order Completed", body, logo_url, site_title)
