"""
AI-generated wealth insights — factual observations about the user's wealth data.
No financial advice. Just observations, patterns, and highlights.
"""
import uuid
import json
from datetime import datetime, timezone, timedelta

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.wealth import Asset, Liability, WealthSnapshot, AllocationSnapshot
from app.services.audit_service import log_event


INSIGHTS_SYSTEM = """You are Wealth Copilot's insight engine. You generate short, factual observations about a user's wealth data.

RULES:
1. ONLY state facts from the provided data. Never invent numbers.
2. Do NOT give financial advice, recommendations, or suggest actions.
3. Use neutral, analytical language. No "you should", "consider buying", etc.
4. Each insight should be 1-2 sentences max.
5. Focus on changes, patterns, concentrations, and milestones.
6. Be specific — cite actual numbers and percentages.

Return ONLY a JSON array of objects with these fields:
- "icon": a single emoji that represents the insight
- "title": short headline (5-8 words)
- "body": 1-2 sentence observation with specific numbers
- "category": one of "milestone", "change", "pattern", "concentration", "health"

Return 4-6 insights. Prioritise the most interesting/notable ones."""


def generate_insights(db: Session, user_id: uuid.UUID) -> list[dict]:
    """Generate AI-powered insights from the user's wealth data."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []

    # Get latest snapshot
    latest = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .first()
    )
    if not latest:
        return []

    # Get previous snapshots for comparison
    snapshots = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .limit(30)
        .all()
    )

    # Get allocation data
    alloc = (
        db.query(AllocationSnapshot)
        .filter(AllocationSnapshot.wealth_snapshot_id == latest.id)
        .first()
    )

    # Get assets
    assets = (
        db.query(Asset)
        .filter(Asset.user_id == user_id)
        .order_by(Asset.current_value.desc())
        .all()
    )
    liabilities = db.query(Liability).filter(Liability.user_id == user_id).all()

    # Build context
    week_ago = None
    month_ago = None
    now = datetime.now(timezone.utc)
    for s in snapshots:
        age = now - s.snapshot_time.replace(tzinfo=timezone.utc) if s.snapshot_time.tzinfo is None else now - s.snapshot_time
        if week_ago is None and age >= timedelta(days=6):
            week_ago = s
        if month_ago is None and age >= timedelta(days=28):
            month_ago = s

    context = {
        "currency": user.base_currency,
        "current": {
            "net_worth": latest.net_worth,
            "total_assets": latest.total_assets,
            "total_liabilities": latest.total_liabilities,
            "liquid_assets": latest.liquid_assets,
            "cash": latest.cash_value,
            "investments": latest.investment_value,
            "property": latest.property_value,
            "crypto": latest.crypto_value,
            "pensions": latest.pension_value,
        },
        "changes": {},
        "allocation": alloc.asset_class_allocations_json if alloc else [],
        "health_score": alloc.health_score if alloc else None,
        "health_breakdown": alloc.health_score_breakdown_json if alloc else {},
        "top_assets": [
            {"name": a.name, "class": a.asset_class, "value": a.current_value}
            for a in assets[:10]
        ],
        "liability_count": len(liabilities),
        "total_debt": sum(l.current_balance for l in liabilities),
        "snapshot_count": len(snapshots),
    }

    if week_ago:
        context["changes"]["7d"] = {
            "net_worth_change": latest.net_worth - week_ago.net_worth,
            "assets_change": latest.total_assets - week_ago.total_assets,
            "liabilities_change": latest.total_liabilities - week_ago.total_liabilities,
        }
    if month_ago:
        context["changes"]["30d"] = {
            "net_worth_change": latest.net_worth - month_ago.net_worth,
            "assets_change": latest.total_assets - month_ago.total_assets,
            "liabilities_change": latest.total_liabilities - month_ago.total_liabilities,
        }

    prompt = f"""Analyze this wealth data and generate insights:

{json.dumps(context, indent=2)}

Return ONLY the JSON array, no other text."""

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=INSIGHTS_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Parse JSON — handle markdown code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        insights = json.loads(text)

        log_event(db, user_id, "ai_insights_generated", {
            "count": len(insights),
            "model": "claude-sonnet-4-20250514",
        })

        return insights
    except Exception:
        return _fallback_insights(latest, alloc, assets, user.base_currency)


def _fallback_insights(
    snapshot: WealthSnapshot,
    alloc: AllocationSnapshot | None,
    assets: list[Asset],
    currency: str,
) -> list[dict]:
    """Generate basic rule-based insights if AI fails."""
    insights = []

    if snapshot.net_worth > 0:
        insights.append({
            "icon": "💰",
            "title": "Net worth is positive",
            "body": f"Your net worth stands at {currency} {snapshot.net_worth:,.0f}, with assets exceeding liabilities.",
            "category": "milestone",
        })

    if snapshot.liquid_assets > 0 and snapshot.total_assets > 0:
        liquid_pct = snapshot.liquid_assets / snapshot.total_assets * 100
        insights.append({
            "icon": "💧",
            "title": f"Liquidity at {liquid_pct:.0f}%",
            "body": f"{currency} {snapshot.liquid_assets:,.0f} of your assets are classified as liquid or highly liquid.",
            "category": "pattern",
        })

    if alloc and alloc.health_score:
        insights.append({
            "icon": "🏥",
            "title": f"Health score: {alloc.health_score}/100",
            "body": f"Your wealth health score is {alloc.health_score} out of 100, based on liquidity, diversification, concentration, and leverage.",
            "category": "health",
        })

    if assets:
        top = assets[0]
        if snapshot.total_assets > 0:
            pct = top.current_value / snapshot.total_assets * 100
            insights.append({
                "icon": "📊",
                "title": f"Largest asset: {top.name}",
                "body": f"{top.name} accounts for {pct:.1f}% of your total assets at {currency} {top.current_value:,.0f}.",
                "category": "concentration",
            })

    return insights
