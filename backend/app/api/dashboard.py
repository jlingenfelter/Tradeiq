import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.analytics import AnalyticsSnapshot
from app.services.portfolio_service import get_portfolio
from app.services.analytics_service import compute_portfolio_analytics
from app.services.warning_service import get_latest_warnings
from app.schemas.dashboard import (
    DashboardResponse, TopHolding, SectorExposure, CountryExposure, TopRisk,
)

router = APIRouter(tags=["dashboard"])


@router.get("/portfolios/{portfolio_id}/dashboard", response_model=DashboardResponse)
def get_dashboard(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)

    # Get latest analytics or compute fresh
    snapshot = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.portfolio_id == portfolio.id)
        .order_by(AnalyticsSnapshot.created_at.desc())
        .first()
    )

    # Recompute if no snapshot or if snapshot is stale (older than 5 minutes)
    stale = False
    if snapshot and snapshot.created_at:
        age = datetime.now(timezone.utc) - snapshot.created_at.replace(tzinfo=timezone.utc)
        stale = age > timedelta(minutes=5)

    if not snapshot or stale:
        try:
            compute_portfolio_analytics(db, str(portfolio.id))
        except Exception:
            pass
        snapshot = (
            db.query(AnalyticsSnapshot)
            .filter(AnalyticsSnapshot.portfolio_id == portfolio.id)
            .order_by(AnalyticsSnapshot.created_at.desc())
            .first()
        )

    if not snapshot:
        return DashboardResponse(
            portfolio_id=str(portfolio.id),
            portfolio_name=portfolio.name,
            base_currency=portfolio.base_currency,
            total_value=0, daily_change=0, daily_change_pct=0,
            health_score=0, health_score_breakdown={},
            top_risks=[], top_holdings=[], sector_exposure=[],
            country_exposure=[], stress_tests=[], ai_summary=None,
        )

    # Build dashboard response
    holdings = snapshot.holdings_detail or []
    top_holdings = [
        TopHolding(
            symbol=h["symbol"], name=h.get("name", h["symbol"]),
            weight=h["weight"], market_value=h["market_value"],
        )
        for h in holdings[:10]
    ]

    sector_exp = [
        SectorExposure(sector=k, weight=v)
        for k, v in (snapshot.sector_exposure or {}).items()
        if k != "Unknown"
    ]

    country_exp = [
        CountryExposure(country=k, weight=v)
        for k, v in (snapshot.country_exposure or {}).items()
        if k != "Unknown"
    ]

    # Get warnings for top risks
    warnings = get_latest_warnings(db, portfolio.id)
    top_risks = [
        TopRisk(
            type=w.warning_type, severity=w.severity,
            title=w.title, description=w.description,
        )
        for w in warnings[:5]
    ]

    # Calculate daily change from holdings
    daily_change = 0.0
    total_value = snapshot.portfolio_snapshot.total_value if snapshot.portfolio_snapshot else 0
    for h in holdings:
        prev = h.get("previous_close")
        if prev and prev > 0:
            daily_change += (h.get("price", 0) - prev) * h.get("quantity", 0)

    daily_change_pct = (daily_change / total_value * 100) if total_value > 0 else 0.0

    return DashboardResponse(
        portfolio_id=str(portfolio.id),
        portfolio_name=portfolio.name,
        base_currency=portfolio.base_currency,
        total_value=round(total_value, 2),
        daily_change=round(daily_change, 2),
        daily_change_pct=round(daily_change_pct, 2),
        health_score=int(snapshot.health_score),
        health_score_breakdown=snapshot.health_score_breakdown or {},
        top_risks=top_risks,
        top_holdings=top_holdings,
        sector_exposure=sector_exp,
        country_exposure=country_exp,
        stress_tests=snapshot.stress_tests or [],
        ai_summary=None,  # Populated in Phase 9
    )
