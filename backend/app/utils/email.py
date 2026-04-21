import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

# ─── Configuration ────────────────────────────

# These pull from your .env file. 
# For Mailtrap Sandbox, use: sandbox.smtp.mailtrap.io
# conf = ConnectionConfig(
#     MAIL_USERNAME = os.getenv("MAIL_USERNAME", "missing_user"), # Fallback string
#     MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "missing_pass"), # Fallback string
#     MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@campusloop.edu"),
#     MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
#     MAIL_SERVER = os.getenv("MAIL_SERVER", "sandbox.smtp.mailtrap.io"),
#     MAIL_STARTTLS = True,
#     MAIL_SSL_TLS = False,
#     USE_CREDENTIALS = True,
#     VALIDATE_CERTS = True
# )
from dotenv import load_dotenv
load_dotenv()
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.ethereal.email"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

# This should point to your frontend (e.g., http://localhost:3000)
BASE_URL = os.getenv("CLIENT_URL", "http://localhost:3000")

# ─── Shared HTML Template ─────────────────────

def email_template(title: str, body_html: str) -> str:
    """Wraps any email body in the CampusLoop branded HTML template."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; margin: 0; padding: 40px 20px; }}
        .card {{ max-width: 520px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 40px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
        .logo {{ font-size: 22px; font-weight: 700; color: #1a56db; margin-bottom: 24px; }}
        h1 {{ font-size: 20px; font-weight: 600; color: #111827; margin: 0 0 12px; }}
        p {{ color: #4b5563; font-size: 15px; line-height: 1.6; margin: 0 0 16px; }}
        .btn {{ display: inline-block; background: #1a56db; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; }}
        .info-box {{ background: #f0f4ff; border-left: 4px solid #1a56db; padding: 12px 16px; border-radius: 4px; margin: 16px 0; }}
        .footer {{ margin-top: 32px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 13px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="logo">🎓 CampusLoop</div>
        <h1>{title}</h1>
        {body_html}
        <div class="footer">
          CampusLoop — The marketplace for college students<br/>
          <small>You're receiving this because you have an account at campusloop.app</small>
        </div>
      </div>
    </body>
    </html>
    """

async def _send(to: str, subject: str, html: str):
    """Internal helper — creates FastMail instance and sends the message."""
    message = MessageSchema(
        subject=subject,
        recipients=[to],
        body=html,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)

# ─── Auth Emails ──────────────────────────────

# async def send_verification_email(email: str, first_name: str, token: str):
#     """Sent after registration — user must click to activate account."""
#     link = f"{BASE_URL}/verify-email/{token}"
#     html = email_template(
#         f"Hi {first_name}, please verify your email",
#         f"""
#         <p>Thanks for joining CampusLoop! One more step — click below to verify
#         your .edu email and activate your account.</p>
#         <p><a href="{link}" class="btn">Verify Email Address</a></p>
#         <p>This link expires in <strong>24 hours</strong>.</p>
#         <p>If you didn't create a CampusLoop account, you can safely ignore this email.</p>
#         """,
#     )
#     await _send(email, "Verify your CampusLoop account", html)
async def send_verification_email(email: str, first_name: str, token: str):
    verify_url = f"http://localhost:8000/api/v1/auth/verify-email/{token}"
    message = MessageSchema(
        subject="Verify your .edu email",
        recipients=[email],
        body=(
            f"Hi {first_name},\n\n"
            f"Click the link below to verify your account:\n\n"
            f"{verify_url}\n\n"
            "This link expires in 24 hours."
        ),
        subtype=MessageType.plain,
    )
    fm = FastMail(conf)
    await fm.send_message(message)

# async def send_password_reset_email(email: str, first_name: str, token: str):
#     """Sent when a user requests a password reset."""
#     link = f"{BASE_URL}/reset-password/{token}"
#     html = email_template(
#         "Reset your password",
#         f"""
#         <p>Hi {first_name}, we received a request to reset your CampusLoop password.</p>
#         <p><a href="{link}" class="btn">Reset Password</a></p>
#         <p>This link expires in <strong>1 hour</strong>.</p>
#         <p>If you didn't request this, you can safely ignore this email —
#         your password will not be changed.</p>
#         """,
#     )
#     await _send(email, "Reset your CampusLoop password", html)
async def send_password_reset_email(email: str, first_name: str, token: str):
    reset_url = f"http://localhost:8000/api/v1/auth/reset-password?token={token}"
    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        body=(
            f"Hi {first_name},\n\n"
            f"Click the link below to reset your password:\n\n"
            f"{reset_url}\n\n"
            "This link expires in 1 hour."
        ),
        subtype=MessageType.plain,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
# ─── Rental Emails ────────────────────────────

async def send_rental_request_email(
    email: str, first_name: str, listing_title: str, renter_name: str
):
    """Notifies listing owner that someone wants to rent their item."""
    html = email_template(
        "You have a new rental request!",
        f"""
        <p>Hi {first_name}, <strong>{renter_name}</strong> has requested to rent your item:</p>
        <div class="info-box"><strong>{listing_title}</strong></div>
        <p>Log in to approve or decline the request.</p>
        <p><a href="{BASE_URL}/dashboard/rentals" class="btn">View Request</a></p>
        """,
    )
    await _send(email, f'New rental request for "{listing_title}"', html)

async def send_rental_approved_email(
    email: str, first_name: str, listing_title: str, owner_name: str
):
    """Notifies renter that their rental request was approved."""
    html = email_template(
        "Your rental request was approved! 🎉",
        f"""
        <p>Hi {first_name}, great news — <strong>{owner_name}</strong> approved your
        rental request for:</p>
        <div class="info-box"><strong>{listing_title}</strong></div>
        <p>Proceed to payment to confirm your rental.</p>
        <p><a href="{BASE_URL}/dashboard/rentals" class="btn">Complete Payment</a></p>
        """,
    )
    await _send(email, f'Rental approved: "{listing_title}"', html)

async def send_rental_declined_email(
    email: str, first_name: str, listing_title: str
):
    """Notifies renter that their rental request was declined."""
    html = email_template(
        "Rental request declined",
        f"""
        <p>Hi {first_name}, unfortunately your rental request for
        <strong>{listing_title}</strong> was declined by the owner.</p>
        <p>Don't worry — there are plenty of other listings available.</p>
        <p><a href="{BASE_URL}/listings?type=RENTAL" class="btn">Browse Rentals</a></p>
        """,
    )
    await _send(email, f'Rental request declined: "{listing_title}"', html)

async def send_item_returned_email(
    email: str, first_name: str, listing_title: str
):
    """Notifies renter that the owner marked their item as returned."""
    html = email_template(
        "Your rental is complete ✅",
        f"""
        <p>Hi {first_name}, your rental of <strong>{listing_title}</strong> has been
        marked as returned by the owner.</p>
        <p>We'd love to know how it went — please leave a review!</p>
        <p><a href="{BASE_URL}/dashboard/rentals" class="btn">Leave a Review</a></p>
        """,
    )
    await _send(email, f'Rental complete: "{listing_title}"', html)

# ─── Order Emails ─────────────────────────────

async def send_order_received_email(
    email: str, first_name: str, listing_title: str, buyer_name: str
):
    """Notifies seller that someone wants to buy their item."""
    html = email_template(
        "Someone wants to buy your item! 🛒",
        f"""
        <p>Hi {first_name}, <strong>{buyer_name}</strong> has placed an order for:</p>
        <div class="info-box"><strong>{listing_title}</strong></div>
        <p>Schedule a meetup to complete the transaction.</p>
        <p><a href="{BASE_URL}/dashboard/orders" class="btn">View Order</a></p>
        """,
    )
    await _send(email, f'New order for "{listing_title}"', html)

async def send_meetup_scheduled_email(
    email: str,
    first_name: str,
    listing_title: str,
    meetup_location: str,
    meetup_time: str,
):
    """Notifies buyer that the seller scheduled a meetup."""
    html = email_template(
        "Meetup scheduled 📍",
        f"""
        <p>Hi {first_name}, the seller has scheduled a meetup for
        <strong>{listing_title}</strong>:</p>
        <div class="info-box">
          📍 <strong>Location:</strong> {meetup_location}<br/>
          🕐 <strong>Time:</strong> {meetup_time}
        </div>
        <p>Once you've received the item, mark the order as complete.</p>
        <p><a href="{BASE_URL}/dashboard/orders" class="btn">View Order</a></p>
        """,
    )
    await _send(email, f'Meetup scheduled for "{listing_title}"', html)

# ─── Booking Emails ───────────────────────────

async def send_booking_request_email(
    email: str, first_name: str, service_title: str, client_name: str, scheduled_at: str
):
    """Notifies service provider of a new booking."""
    html = email_template(
        "New booking request 📅",
        f"""
        <p>Hi {first_name}, <strong>{client_name}</strong> has booked your service:</p>
        <div class="info-box">
          <strong>{service_title}</strong><br/>
          🕐 Scheduled: {scheduled_at}
        </div>
        <p>Confirm or decline the booking from your dashboard.</p>
        <p><a href="{BASE_URL}/dashboard/services" class="btn">View Booking</a></p>
        """,
    )
    await _send(email, f'New booking: "{service_title}"', html)

async def send_booking_confirmed_email(
    email: str, first_name: str, service_title: str, scheduled_at: str
):
    """Notifies client that their service booking was confirmed."""
    html = email_template(
        "Booking confirmed! ✅",
        f"""
        <p>Hi {first_name}, your booking has been confirmed:</p>
        <div class="info-box">
          <strong>{service_title}</strong><br/>
          🕐 Scheduled: {scheduled_at}
        </div>
        <p><a href="{BASE_URL}/dashboard/bookings" class="btn">View Booking</a></p>
        """,
    )
    await _send(email, f'Booking confirmed: "{service_title}"', html)

# ─── Message Notification Email ───────────────

async def send_new_message_email(
    email: str, first_name: str, sender_name: str, message_preview: str, conversation_id: str
):
    """Notifies a user they have a new message."""
    preview = message_preview[:100] + "..." if len(message_preview) > 100 else message_preview
    html = email_template(
        f"New message from {sender_name}",
        f"""
        <p>Hi {first_name}, you have a new message from <strong>{sender_name}</strong>:</p>
        <div class="info-box">"{preview}"</div>
        <p><a href="{BASE_URL}/messages/{conversation_id}" class="btn">Reply</a></p>
        """,
    )
    await _send(email, f"New message from {sender_name}", html)

# ─── Review Notification Email ────────────────

async def send_new_review_email(
    email: str, first_name: str, reviewer_name: str, rating: int, listing_title: str
):
    """Notifies a user that they received a new review."""
    stars = "⭐" * rating
    html = email_template(
        "You got a new review!",
        f"""
        <p>Hi {first_name}, <strong>{reviewer_name}</strong> left you a review for
        <strong>{listing_title}</strong>:</p>
        <div class="info-box">{stars} ({rating}/5)</div>
        <p><a href="{BASE_URL}/profile" class="btn">View Your Profile</a></p>
        """,
    )
    await _send(email, f"New {rating}-star review from {reviewer_name}", html)