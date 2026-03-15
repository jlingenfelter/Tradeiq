"""Tier-gating dependency for FastAPI endpoints."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

TIER_HIERARCHY = {"free": 0, "pro": 1, "family": 2}


def get_user_tier(db: Session, user_id) -> str:
    """Return the user's current subscription tier."""
    from app.models.subscription import Subscription
    sub = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status.in_(["active", "trialing"]),
    ).first()
    if sub:
        return sub.tier
    return "free"


def require_tier(minimum_tier: str):
    """FastAPI Depends() factory — returns 403 if user's tier < required."""
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        user_tier = get_user_tier(db, current_user.id)
        if TIER_HIERARCHY.get(user_tier, 0) < TIER_HIERARCHY.get(minimum_tier, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a {minimum_tier.title()} plan. Please upgrade.",
            )
        return current_user
    return dependency


require_pro = require_tier("pro")
require_family = require_tier("family")
