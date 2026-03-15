"""
Smart alerts — automatically generated notifications based on wealth data changes.
These are factual triggers, not advice.
"""
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wealth import WealthSnapshot, AllocationSnapshot, Asset
from app.models.goal import WealthGoal


def generate_smart_alerts(db: Session, user_id: uuid.UUID) -> list[dict]:
    """Generate smart alerts based on current wealth data and history."""
    alerts = []

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return alerts

    currency = user.base_currency

    # Get snapshots
    snapshots = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .limit(60)
        .all()
    )

    if not snapshots:
        return alerts

    latest = snapshots[0]
    now = datetime.now(timezone.utc)

    # Find comparison snapshots
    prev_week = None
    prev_month = None
    for s in snapshots[1:]:
        age = now - (s.snapshot_time.replace(tzinfo=timezone.utc) if s.snapshot_time.tzinfo is None else s.snapshot_time)
        if prev_week is None and age >= timedelta(days=6):
            prev_week = s
        if prev_month is None and age >= timedelta(days=28):
            prev_month = s

    # ── Milestone alerts ──
    milestones = [10_000, 25_000, 50_000, 75_000, 100_000, 150_000, 200_000,
                  250_000, 300_000, 500_000, 750_000, 1_000_000, 2_000_000, 5_000_000]
    if prev_week:
        for m in milestones:
            if prev_week.net_worth < m <= latest.net_worth:
                alerts.append({
                    "type": "milestone",
                    "icon": "🎯",
                    "title": f"Net worth crossed {currency} {m:,.0f}!",
                    "body": f"Your net worth has reached {currency} {latest.net_worth:,.0f}.",
                    "severity": "success",
                    "timestamp": latest.snapshot_time.isoformat(),
                })

    # ── Big weekly change ──
    if prev_week:
        change = latest.net_worth - prev_week.net_worth
        if prev_week.net_worth > 0:
            change_pct = (change / prev_week.net_worth) * 100
            if abs(change_pct) >= 5:
                direction = "increased" if change > 0 else "decreased"
                alerts.append({
                    "type": "big_change",
                    "icon": "📈" if change > 0 else "📉",
                    "title": f"Net worth {direction} {abs(change_pct):.1f}% this week",
                    "body": f"Changed by {currency} {change:+,.0f} (from {currency} {prev_week.net_worth:,.0f} to {currency} {latest.net_worth:,.0f}).",
                    "severity": "info",
                    "timestamp": latest.snapshot_time.isoformat(),
                })

    # ── Monthly trend ──
    if prev_month:
        change = latest.net_worth - prev_month.net_worth
        if prev_month.net_worth > 0:
            change_pct = (change / prev_month.net_worth) * 100
            if change_pct >= 3:
                alerts.append({
                    "type": "trend",
                    "icon": "🔥",
                    "title": f"Strong month: +{change_pct:.1f}% growth",
                    "body": f"Net worth grew by {currency} {change:,.0f} over the past 30 days.",
                    "severity": "success",
                    "timestamp": latest.snapshot_time.isoformat(),
                })
            elif change_pct <= -5:
                alerts.append({
                    "type": "trend",
                    "icon": "⚠️",
                    "title": f"Net worth down {abs(change_pct):.1f}% this month",
                    "body": f"Net worth decreased by {currency} {abs(change):,.0f} over the past 30 days.",
                    "severity": "warning",
                    "timestamp": latest.snapshot_time.isoformat(),
                })

    # ── Concentration alerts ──
    alloc = (
        db.query(AllocationSnapshot)
        .filter(AllocationSnapshot.wealth_snapshot_id == latest.id)
        .first()
    )
    if alloc and alloc.asset_class_allocations_json:
        for a in alloc.asset_class_allocations_json:
            if a.get("weight", 0) >= 50:
                alerts.append({
                    "type": "concentration",
                    "icon": "⚖️",
                    "title": f"{a['category']} is {a['weight']:.0f}% of assets",
                    "body": f"A single category exceeding 50% represents significant concentration.",
                    "severity": "warning",
                    "timestamp": latest.snapshot_time.isoformat(),
                })
                break

    # ── Health score alert ──
    if alloc and alloc.health_score is not None:
        if alloc.health_score < 40:
            alerts.append({
                "type": "health",
                "icon": "🏥",
                "title": f"Health score is low ({alloc.health_score}/100)",
                "body": "Your wealth health score has dropped below 40. Review your liquidity, diversification, and leverage.",
                "severity": "warning",
                "timestamp": latest.snapshot_time.isoformat(),
            })

    # ── Emergency fund check ──
    if latest.total_liabilities > 0 and latest.cash_value > 0:
        months_covered = latest.cash_value / max(latest.total_liabilities / 12, 1)
        if months_covered < 3:
            alerts.append({
                "type": "emergency_fund",
                "icon": "🛟",
                "title": f"Cash covers ~{months_covered:.1f} months of liabilities",
                "body": f"Cash holdings of {currency} {latest.cash_value:,.0f} cover less than 3 months of annualized liabilities.",
                "severity": "info",
                "timestamp": latest.snapshot_time.isoformat(),
            })

    # ── Goal completion alerts ──
    goals = db.query(WealthGoal).filter(
        WealthGoal.user_id == user_id,
        WealthGoal.is_active.is_(True),
    ).all()

    for goal in goals:
        if goal.goal_type == "net_worth" and latest.net_worth >= goal.target_amount:
            alerts.append({
                "type": "goal_reached",
                "icon": goal.emoji or "🏆",
                "title": f"Goal reached: {goal.name}!",
                "body": f"Your net worth of {currency} {latest.net_worth:,.0f} has reached your target of {currency} {goal.target_amount:,.0f}.",
                "severity": "success",
                "timestamp": latest.snapshot_time.isoformat(),
            })

    # ── Stale data alert ──
    stale_assets = []
    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    for a in assets:
        if a.valuation_source == "manual" and a.valuation_date:
            vd = a.valuation_date.replace(tzinfo=timezone.utc) if a.valuation_date.tzinfo is None else a.valuation_date
            if (now - vd) > timedelta(days=60):
                stale_assets.append(a.name)

    if stale_assets:
        alerts.append({
            "type": "stale_data",
            "icon": "📅",
            "title": f"{len(stale_assets)} asset(s) need updating",
            "body": f"These assets haven't been updated in 60+ days: {', '.join(stale_assets[:3])}{'...' if len(stale_assets) > 3 else ''}.",
            "severity": "info",
            "timestamp": now.isoformat(),
        })

    # Sort: success first, then warning, then info
    severity_order = {"success": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))

    return alerts
