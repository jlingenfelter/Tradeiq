from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.notification import NotificationPreference

router = APIRouter(prefix="/notifications", tags=["notifications"])

VALID_NOTIFICATION_TYPES = {"weekly_recap", "goal_milestone", "large_change", "stale_data"}


class PreferenceUpdateRequest(BaseModel):
    notification_type: str
    enabled: bool


# ── GET /notifications/preferences ──────────────────────────────────────
@router.get("/preferences")
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification preferences for the current user."""
    prefs = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id,
    ).all()

    # Build a complete set — return defaults for missing types
    existing = {p.notification_type: p for p in prefs}
    result = []
    for ntype in sorted(VALID_NOTIFICATION_TYPES):
        if ntype in existing:
            p = existing[ntype]
            result.append({
                "id": str(p.id),
                "notification_type": p.notification_type,
                "channel": p.channel,
                "enabled": p.enabled,
            })
        else:
            result.append({
                "id": None,
                "notification_type": ntype,
                "channel": "email",
                "enabled": True,
            })

    return {"preferences": result}


# ── PATCH /notifications/preferences ────────────────────────────────────
@router.patch("/preferences")
def update_preference(
    body: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a notification preference (or create it if it doesn't exist)."""
    from app.core.exceptions import BadRequestError

    if body.notification_type not in VALID_NOTIFICATION_TYPES:
        raise BadRequestError(
            f"Invalid notification_type. Must be one of: {', '.join(sorted(VALID_NOTIFICATION_TYPES))}"
        )

    pref = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id,
        NotificationPreference.notification_type == body.notification_type,
    ).first()

    if pref:
        pref.enabled = body.enabled
    else:
        pref = NotificationPreference(
            user_id=current_user.id,
            notification_type=body.notification_type,
            channel="email",
            enabled=body.enabled,
        )
        db.add(pref)

    db.commit()
    db.refresh(pref)

    return {
        "id": str(pref.id),
        "notification_type": pref.notification_type,
        "channel": pref.channel,
        "enabled": pref.enabled,
    }
