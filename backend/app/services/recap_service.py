"""Weekly wealth recap — fun, motivating summary of net worth changes."""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.wealth import WealthSnapshot
from app.models.user import User


def generate_weekly_recap(db: Session, user_id: uuid.UUID) -> dict | None:
    """Generate a fun weekly recap from snapshot history."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Get latest snapshot
    latest = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .first()
    )
    if not latest:
        return None

    # Find snapshot closest to 7 days ago
    week_snapshot = (
        db.query(WealthSnapshot)
        .filter(
            WealthSnapshot.user_id == user_id,
            WealthSnapshot.snapshot_time <= week_ago,
        )
        .order_by(WealthSnapshot.snapshot_time.desc())
        .first()
    )

    # Find snapshot closest to 30 days ago
    month_snapshot = (
        db.query(WealthSnapshot)
        .filter(
            WealthSnapshot.user_id == user_id,
            WealthSnapshot.snapshot_time <= month_ago,
        )
        .order_by(WealthSnapshot.snapshot_time.desc())
        .first()
    )

    # All snapshots for streak calculation
    all_snapshots = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .limit(90)
        .all()
    )

    currency = user.base_currency

    # Weekly change
    weekly_change = 0.0
    weekly_change_pct = 0.0
    if week_snapshot:
        weekly_change = latest.net_worth - week_snapshot.net_worth
        if week_snapshot.net_worth != 0:
            weekly_change_pct = (weekly_change / abs(week_snapshot.net_worth)) * 100

    # Monthly change
    monthly_change = 0.0
    monthly_change_pct = 0.0
    if month_snapshot:
        monthly_change = latest.net_worth - month_snapshot.net_worth
        if month_snapshot.net_worth != 0:
            monthly_change_pct = (monthly_change / abs(month_snapshot.net_worth)) * 100

    # Category movers (what grew/shrank the most this week)
    category_changes = []
    if week_snapshot:
        categories = [
            ("Cash", latest.cash_value, week_snapshot.cash_value),
            ("Stocks & Shares", latest.investment_value, week_snapshot.investment_value),
            ("Property", latest.property_value, week_snapshot.property_value),
            ("Crypto", latest.crypto_value, week_snapshot.crypto_value),
            ("Business", latest.business_value, week_snapshot.business_value),
            ("Pensions", latest.pension_value, week_snapshot.pension_value),
        ]
        for name, current, previous in categories:
            if current > 0 or previous > 0:
                change = current - previous
                category_changes.append({
                    "category": name,
                    "current": round(current, 2),
                    "previous": round(previous, 2),
                    "change": round(change, 2),
                    "change_pct": round((change / previous * 100) if previous != 0 else 0, 1),
                })
        category_changes.sort(key=lambda x: abs(x["change"]), reverse=True)

    # Growth streak: consecutive snapshots where net worth increased
    growth_streak = 0
    for i in range(len(all_snapshots) - 1):
        if all_snapshots[i].net_worth >= all_snapshots[i + 1].net_worth:
            growth_streak += 1
        else:
            break

    # Per-hour earnings (fun stat)
    hours_in_week = 168
    per_hour = weekly_change / hours_in_week if weekly_change != 0 else 0
    per_day = weekly_change / 7 if weekly_change != 0 else 0

    # Fun headline
    headline = _generate_headline(weekly_change, weekly_change_pct, growth_streak, currency)

    # Debt change
    debt_change = 0.0
    if week_snapshot:
        debt_change = latest.total_liabilities - week_snapshot.total_liabilities

    return {
        "currency": currency,
        "net_worth": round(latest.net_worth, 2),
        "weekly_change": round(weekly_change, 2),
        "weekly_change_pct": round(weekly_change_pct, 2),
        "monthly_change": round(monthly_change, 2),
        "monthly_change_pct": round(monthly_change_pct, 2),
        "per_hour": round(per_hour, 2),
        "per_day": round(per_day, 2),
        "growth_streak": growth_streak,
        "headline": headline,
        "top_movers": category_changes[:3],
        "debt_change": round(debt_change, 2),
        "total_assets": round(latest.total_assets, 2),
        "total_liabilities": round(latest.total_liabilities, 2),
        "snapshot_count": len(all_snapshots),
    }


def _generate_headline(change: float, change_pct: float, streak: int, currency: str) -> str:
    """Generate a fun, motivating headline for the recap."""
    if change > 0:
        if change_pct > 5:
            return "Incredible week! Your wealth is on fire"
        if change_pct > 2:
            return "Great week! Solid growth across the board"
        if change_pct > 0.5:
            return "Steady progress this week"
        return "Small gains add up over time"
    elif change < 0:
        if change_pct < -5:
            return "Tough week, but markets bounce back"
        if change_pct < -2:
            return "A dip this week — stay the course"
        return "Slight pullback, nothing to worry about"
    else:
        return "Holding steady this week"
