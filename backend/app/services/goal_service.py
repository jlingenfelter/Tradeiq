"""Goal tracking — progress calculation, projected dates, milestones."""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.goal import WealthGoal
from app.models.wealth import WealthSnapshot
from app.models.user import User


GOAL_TYPE_VALUE_MAP = {
    "net_worth": "net_worth",
    "savings": "cash_value",
    "investment": "investment_value",
    "emergency_fund": "liquid_assets",
}


def _get_current_value(goal: WealthGoal, snapshot: WealthSnapshot | None) -> float:
    """Get the current value for a goal type from the latest snapshot."""
    if not snapshot:
        return 0.0
    if goal.goal_type == "debt_payoff":
        return snapshot.total_liabilities
    field = GOAL_TYPE_VALUE_MAP.get(goal.goal_type, "net_worth")
    return getattr(snapshot, field, 0.0)


def _compute_goal_progress(goal: WealthGoal, current_value: float, history: list[WealthSnapshot]) -> dict:
    """Compute progress, pace, and projected completion for a goal."""
    now = datetime.now(timezone.utc)

    # For debt_payoff, progress = how much debt has been reduced
    if goal.goal_type == "debt_payoff":
        if not history:
            progress_pct = 0.0
        else:
            starting_debt = history[0].total_liabilities if history else current_value
            if starting_debt <= 0:
                progress_pct = 100.0
            else:
                reduced = starting_debt - current_value
                progress_pct = min(100.0, max(0.0, (reduced / (starting_debt - goal.target_amount)) * 100)) if starting_debt > goal.target_amount else 100.0
        remaining = max(0, current_value - goal.target_amount)
    else:
        progress_pct = min(100.0, max(0.0, (current_value / goal.target_amount * 100))) if goal.target_amount > 0 else 0.0
        remaining = max(0, goal.target_amount - current_value)

    # Days remaining
    days_remaining = None
    if goal.target_date:
        delta = goal.target_date.replace(tzinfo=timezone.utc) - now if goal.target_date.tzinfo is None else goal.target_date - now
        days_remaining = max(0, delta.days)

    # Pace: monthly growth rate from snapshot history
    monthly_growth = 0.0
    projected_date = None
    on_track = None

    if len(history) >= 2:
        oldest = history[0]
        newest = history[-1]
        oldest_time = oldest.snapshot_time.replace(tzinfo=timezone.utc) if oldest.snapshot_time.tzinfo is None else oldest.snapshot_time
        newest_time = newest.snapshot_time.replace(tzinfo=timezone.utc) if newest.snapshot_time.tzinfo is None else newest.snapshot_time
        days_span = (newest_time - oldest_time).days
        if days_span > 0:
            if goal.goal_type == "debt_payoff":
                total_change = oldest.total_liabilities - newest.total_liabilities
            else:
                old_val = getattr(oldest, GOAL_TYPE_VALUE_MAP.get(goal.goal_type, "net_worth"), 0)
                new_val = getattr(newest, GOAL_TYPE_VALUE_MAP.get(goal.goal_type, "net_worth"), 0)
                total_change = new_val - old_val
            monthly_growth = total_change / days_span * 30.44  # avg days per month

            # Project completion
            if monthly_growth > 0 and remaining > 0:
                months_to_go = remaining / monthly_growth
                projected_date = (now + timedelta(days=months_to_go * 30.44)).isoformat()

                if goal.target_date:
                    target_dt = goal.target_date.replace(tzinfo=timezone.utc) if goal.target_date.tzinfo is None else goal.target_date
                    on_track = (now + timedelta(days=months_to_go * 30.44)) <= target_dt

    # Milestones
    milestones = []
    milestone_pcts = [10, 25, 50, 75, 90, 100]
    for pct in milestone_pcts:
        reached = progress_pct >= pct
        milestones.append({"pct": pct, "reached": reached})

    # Fun stats
    if goal.goal_type == "debt_payoff":
        amount_label = f"remaining to pay off"
    else:
        amount_label = f"to go"

    return {
        "progress_pct": round(progress_pct, 1),
        "current_value": round(current_value, 2),
        "remaining": round(remaining, 2),
        "amount_label": amount_label,
        "monthly_growth": round(monthly_growth, 2),
        "projected_date": projected_date,
        "on_track": on_track,
        "days_remaining": days_remaining,
        "milestones": milestones,
    }


def get_goals(db: Session, user_id: uuid.UUID) -> list[dict]:
    """Get all goals with progress data."""
    goals = db.query(WealthGoal).filter(
        WealthGoal.user_id == user_id,
        WealthGoal.is_active == True,
    ).order_by(WealthGoal.created_at.desc()).all()

    # Get latest snapshot for current values
    latest_snapshot = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .first()
    )

    # Get snapshot history for pace calculation (last 90 days)
    history = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.asc())
        .all()
    )

    results = []
    for goal in goals:
        current_value = _get_current_value(goal, latest_snapshot)
        progress = _compute_goal_progress(goal, current_value, history)

        results.append({
            "id": str(goal.id),
            "name": goal.name,
            "emoji": goal.emoji,
            "goal_type": goal.goal_type,
            "target_amount": goal.target_amount,
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
            "currency": goal.currency,
            "notes": goal.notes,
            **progress,
        })

    return results


def create_goal(db: Session, user_id: uuid.UUID, data: dict) -> dict:
    """Create a new wealth goal."""
    user = db.query(User).filter(User.id == user_id).first()

    goal = WealthGoal(
        user_id=user_id,
        name=data["name"],
        target_amount=data["target_amount"],
        target_date=data.get("target_date"),
        goal_type=data.get("goal_type", "net_worth"),
        currency=data.get("currency", user.base_currency if user else "USD"),
        emoji=data.get("emoji", "🎯"),
        notes=data.get("notes"),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return {
        "id": str(goal.id),
        "name": goal.name,
        "emoji": goal.emoji,
        "goal_type": goal.goal_type,
        "target_amount": goal.target_amount,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "currency": goal.currency,
    }


def update_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, data: dict) -> dict:
    """Update an existing goal."""
    goal = db.query(WealthGoal).filter(
        WealthGoal.id == goal_id,
        WealthGoal.user_id == user_id,
    ).first()
    if not goal:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Goal not found")

    for field in ("name", "target_amount", "target_date", "goal_type", "currency", "emoji", "notes", "is_active"):
        if field in data:
            setattr(goal, field, data[field])

    db.commit()
    return {"id": str(goal.id), "updated": True}


def delete_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
    """Delete a goal."""
    goal = db.query(WealthGoal).filter(
        WealthGoal.id == goal_id,
        WealthGoal.user_id == user_id,
    ).first()
    if not goal:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Goal not found")

    db.delete(goal)
    db.commit()
    return {"deleted": True}
