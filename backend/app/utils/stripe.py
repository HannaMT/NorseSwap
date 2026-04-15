"""
Stripe Utilities
================
Shared helpers for Stripe payment operations.
"""

import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
PLATFORM_FEE_PERCENT = settings.STRIPE_PLATFORM_FEE_PERCENT


def calculate_platform_fee(amount_cents: int) -> int:
    """Returns the platform fee in cents (e.g. 5% of $20.00 = 100 cents)"""
    return int(amount_cents * (PLATFORM_FEE_PERCENT / 100))


async def create_stripe_payment_intent(
    amount_cents: int,
    metadata: dict,
    destination_account_id: str = None,
    description: str = "",
) -> stripe.PaymentIntent:
    """
    Create a Stripe PaymentIntent.
    If destination_account_id is provided, uses Stripe Connect
    to route funds to the seller minus the platform fee.
    """
    kwargs = {
        "amount": amount_cents,
        "currency": "usd",
        "description": description,
        "metadata": metadata,
        "automatic_payment_methods": {"enabled": True},
    }

    if destination_account_id:
        fee = calculate_platform_fee(amount_cents)
        kwargs["transfer_data"] = {"destination": destination_account_id}
        kwargs["application_fee_amount"] = fee

    return stripe.PaymentIntent.create(**kwargs)