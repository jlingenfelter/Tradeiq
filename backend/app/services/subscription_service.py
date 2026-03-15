"""Stripe subscription management service."""

from datetime import datetime, timezone

import stripe
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.subscription import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_stripe_customer(db: Session, user: User) -> str:
    """Get existing Stripe customer ID or create one."""
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if sub and sub.stripe_customer_id:
        return sub.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": str(user.id)},
    )

    if not sub:
        sub = Subscription(
            user_id=user.id,
            stripe_customer_id=customer.id,
            tier="free",
            status="active",
        )
        db.add(sub)
    else:
        sub.stripe_customer_id = customer.id

    db.commit()
    return customer.id


def create_checkout_session(db: Session, user: User, tier: str) -> str:
    """Create a Stripe Checkout session and return the URL."""
    price_map = {
        "pro": settings.STRIPE_PRO_PRICE_ID,
        "family": settings.STRIPE_FAMILY_PRICE_ID,
    }
    price_id = price_map.get(tier)
    if not price_id:
        raise ValueError(f"Invalid tier: {tier}")

    customer_id = get_or_create_stripe_customer(db, user)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/settings?billing=success",
        cancel_url=f"{settings.FRONTEND_URL}/pricing?billing=canceled",
        metadata={"user_id": str(user.id), "tier": tier},
    )
    return session.url


def create_billing_portal_session(db: Session, user: User) -> str:
    """Create a Stripe Customer Portal session for managing subscription."""
    customer_id = get_or_create_stripe_customer(db, user)
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.FRONTEND_URL}/settings",
    )
    return session.url


def get_subscription_info(db: Session, user_id) -> dict:
    """Get the current subscription info for a user."""
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        return {
            "tier": "free",
            "status": "active",
            "current_period_end": None,
            "cancel_at_period_end": False,
        }
    return {
        "tier": sub.tier,
        "status": sub.status,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "cancel_at_period_end": sub.cancel_at_period_end,
    }


def handle_webhook_event(db: Session, event: dict):
    """Process Stripe webhook events."""
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(db, data)
    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(db, data)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(db, data)
    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(db, data)


def _handle_checkout_completed(db: Session, session_data: dict):
    """Handle successful checkout — activate subscription."""
    customer_id = session_data.get("customer")
    subscription_id = session_data.get("subscription")
    tier = session_data.get("metadata", {}).get("tier", "pro")

    sub = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()

    if sub:
        sub.stripe_subscription_id = subscription_id
        sub.tier = tier
        sub.status = "active"
        db.commit()


def _handle_subscription_updated(db: Session, sub_data: dict):
    """Handle subscription changes (upgrade, downgrade, renewal)."""
    stripe_sub_id = sub_data.get("id")
    sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()

    if not sub:
        return

    sub.status = sub_data.get("status", sub.status)
    sub.cancel_at_period_end = sub_data.get("cancel_at_period_end", False)

    period_start = sub_data.get("current_period_start")
    period_end = sub_data.get("current_period_end")
    if period_start:
        sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

    # Detect tier from price
    items = sub_data.get("items", {}).get("data", [])
    if items:
        price_id = items[0].get("price", {}).get("id", "")
        if price_id == settings.STRIPE_FAMILY_PRICE_ID:
            sub.tier = "family"
        elif price_id == settings.STRIPE_PRO_PRICE_ID:
            sub.tier = "pro"

    db.commit()


def _handle_subscription_deleted(db: Session, sub_data: dict):
    """Handle subscription cancellation."""
    stripe_sub_id = sub_data.get("id")
    sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()

    if sub:
        sub.tier = "free"
        sub.status = "canceled"
        sub.stripe_subscription_id = None
        db.commit()


def _handle_payment_failed(db: Session, invoice_data: dict):
    """Handle failed payment."""
    customer_id = invoice_data.get("customer")
    sub = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()

    if sub:
        sub.status = "past_due"
        db.commit()
