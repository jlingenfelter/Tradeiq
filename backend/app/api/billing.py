"""Billing & subscription endpoints."""

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import stripe

from app.config import settings
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.subscription_service import (
    create_checkout_session,
    create_billing_portal_session,
    get_subscription_info,
    handle_webhook_event,
)

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    tier: str  # "pro" or "family"


@router.get("/subscription")
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_subscription_info(db, current_user.id)


@router.post("/checkout")
def create_checkout(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.tier not in ("pro", "family"):
        raise HTTPException(400, "Invalid tier. Must be 'pro' or 'family'.")
    url = create_checkout_session(db, current_user, body.tier)
    return {"url": url}


@router.post("/portal")
def create_portal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = create_billing_portal_session(db, current_user)
    return {"url": url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events. No auth required — verified by signature."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook signature")

    db = next(get_db())
    try:
        handle_webhook_event(db, event)
    finally:
        db.close()

    return {"status": "ok"}
