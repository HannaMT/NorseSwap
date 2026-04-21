"""
Payments Router
===============
Handles Stripe payment intents for rentals, orders, and bookings.
Also handles Stripe Connect onboarding so sellers can receive payouts.

Flow:
  1. Client calls POST /payments/intent with type + reference_id
  2. Server creates a Stripe PaymentIntent and returns client_secret
  3. Client uses client_secret to complete payment with Stripe.js
  4. Stripe sends a webhook → server updates the rental/order/booking status
"""

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_verified_user
from app.core.config import settings
from app.models.models import (
    User, Rental, Order, ServiceBooking,
    RentalStatus, OrderStatus, BookingStatus,
)
from app.schemas.schemas import PaymentIntentCreate, PaymentIntentResponse, MessageOnlyResponse
from app.utils.stripe import create_stripe_payment_intent

stripe.api_key = settings.STRIPE_SECRET_KEY
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    body: PaymentIntentCreate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe PaymentIntent for a rental, order, or booking.
    Returns a client_secret that the frontend uses with Stripe.js to collect payment.
    """
    if body.type == "rental":
        result = await db.execute(select(Rental).where(Rental.id == body.reference_id))
        obj = result.scalar_one_or_none()
        if not obj or obj.renter_id != current_user.id:
            raise HTTPException(404, "Rental not found.")
        if obj.status != RentalStatus.APPROVED:
            raise HTTPException(400, "Rental must be approved before payment.")
        amount_cents = int(obj.total_price * 100)
        metadata = {"type": "rental", "rental_id": obj.id}

        # Load seller's Stripe account
        seller = await db.get(User, obj.owner_id)
        destination = seller.stripe_account_id if seller else None

    elif body.type == "order":
        result = await db.execute(select(Order).where(Order.id == body.reference_id))
        obj = result.scalar_one_or_none()
        if not obj or obj.buyer_id != current_user.id:
            raise HTTPException(404, "Order not found.")
        amount_cents = int(obj.total_amount * 100)
        metadata = {"type": "order", "order_id": obj.id}

        seller = await db.get(User, obj.seller_id)
        destination = seller.stripe_account_id if seller else None

    elif body.type == "booking":
        result = await db.execute(select(ServiceBooking).where(ServiceBooking.id == body.reference_id))
        obj = result.scalar_one_or_none()
        if not obj or obj.client_id != current_user.id:
            raise HTTPException(404, "Booking not found.")
        if obj.status != BookingStatus.CONFIRMED:
            raise HTTPException(400, "Booking must be confirmed before payment.")
        amount_cents = int(obj.total_amount * 100)
        metadata = {"type": "booking", "booking_id": obj.id}

        provider = await db.get(User, obj.provider_id)
        destination = provider.stripe_account_id if provider else None

    else:
        raise HTTPException(400, "Invalid payment type. Must be 'rental', 'order', or 'booking'.")

    intent = await create_stripe_payment_intent(
        amount_cents=amount_cents,
        metadata=metadata,
        destination_account_id=destination,
    )

    # Save the payment intent ID so we can match the webhook later
    obj.stripe_payment_intent_id = intent.id

    return {"client_secret": intent.client_secret}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Stripe sends events here after payment succeeds or fails.
    We update the rental/order/booking status accordingly.

    IMPORTANT: This endpoint must receive raw bytes (not parsed JSON).
    The raw body is needed to verify the Stripe signature.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid Stripe signature.")

    if event.type == "payment_intent.succeeded":
        pi = event.data.object
        meta = pi.metadata
        ptype = meta.get("type")

        if ptype == "rental":
            result = await db.execute(select(Rental).where(Rental.id == meta.get("rental_id")))
            rental = result.scalar_one_or_none()
            if rental:
                rental.status = RentalStatus.ACTIVE

        elif ptype == "order":
            result = await db.execute(select(Order).where(Order.id == meta.get("order_id")))
            order = result.scalar_one_or_none()
            if order:
                order.status = OrderStatus.PAID

        elif ptype == "booking":
            result = await db.execute(select(ServiceBooking).where(ServiceBooking.id == meta.get("booking_id")))
            booking = result.scalar_one_or_none()
            if booking:
                booking.status = BookingStatus.CONFIRMED

    elif event.type == "payment_intent.payment_failed":
        pi = event.data.object
        meta = pi.metadata
        ptype = meta.get("type")

        if ptype == "rental":
            result = await db.execute(select(Rental).where(Rental.id == meta.get("rental_id")))
            rental = result.scalar_one_or_none()
            if rental:
                rental.status = RentalStatus.CANCELLED

        elif ptype == "order":
            result = await db.execute(select(Order).where(Order.id == meta.get("order_id")))
            order = result.scalar_one_or_none()
            if order:
                order.status = OrderStatus.CANCELLED

    return {"received": True}


@router.post("/connect", response_model=dict)
async def create_stripe_connect_account(
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Onboard a student as a seller via Stripe Connect Express.
    Returns a URL to complete Stripe's onboarding flow.
    After completion, the user can receive payouts directly.
    """
    user = await db.get(User, current_user.id)

    # Create Stripe account if it doesn't exist yet
    if not user.stripe_account_id:
        account = stripe.Account.create(
            type="express",
            email=user.email,
            metadata={"user_id": user.id, "university": user.university},
        )
        user.stripe_account_id = account.id
        await db.flush()

    # Generate an onboarding link (expires after a short time)
    link = stripe.AccountLink.create(
        account=user.stripe_account_id,
        refresh_url=f"{settings.CLIENT_URL}/settings/payments?reauth=true",
        return_url=f"{settings.CLIENT_URL}/settings/payments?connected=true",
        type="account_onboarding",
    )

    return {"url": link.url}


@router.get("/connect/status")
async def get_connect_status(
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether the current user has completed Stripe Connect onboarding."""
    user = await db.get(User, current_user.id)

    if not user.stripe_account_id:
        return {"connected": False, "stripe_account_id": None}

    # Check account status with Stripe
    try:
        account = stripe.Account.retrieve(user.stripe_account_id)
        is_ready = account.charges_enabled and account.payouts_enabled
        return {
            "connected": True,
            "stripe_account_id": user.stripe_account_id,
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled,
            "ready_to_receive": is_ready,
        }
    except stripe.error.StripeError:
        return {"connected": False, "stripe_account_id": user.stripe_account_id}