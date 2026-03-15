import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.analytics import AnalyticsSnapshot
from app.services.portfolio_service import get_portfolio
from app.services.analytics_service import compute_portfolio_analytics
from app.services.audit_service import log_event

router = APIRouter(tags=["analytics"])


@router.get("/portfolios/{portfolio_id}/analytics/latest")
def get_latest_analytics(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    # Get the most recent analytics snapshot
    snapshot = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.portfolio_id == portfolio.id)
        .order_by(AnalyticsSnapshot.created_at.desc())
        .first()
    )
    if not snapshot:
        # Compute on first access
        result = compute_portfolio_analytics(db, str(portfolio.id))
        return result

    return {
        "analytics_snapshot_id": str(snapshot.id),
        "portfolio_snapshot_id": str(snapshot.portfolio_snapshot_id),
        "total_value": snapshot.portfolio_snapshot.total_value,
        "health_score": snapshot.health_score,
        "health_score_breakdown": snapshot.health_score_breakdown,
        "top_holding_weight": snapshot.top_holding_weight,
        "top_3_weight": snapshot.top_3_weight,
        "top_5_weight": snapshot.top_5_weight,
        "sector_exposure": snapshot.sector_exposure,
        "country_exposure": snapshot.country_exposure,
        "stress_tests": snapshot.stress_tests,
        "holdings": snapshot.holdings_detail,
        "diversification_score": snapshot.diversification_score,
    }


@router.get("/portfolios/{portfolio_id}/analytics/history")
def get_analytics_history(
    portfolio_id: uuid.UUID,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    snapshots = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.portfolio_id == portfolio.id)
        .order_by(AnalyticsSnapshot.created_at.desc())
        .limit(limit)
        .all()
    )
    return [{
        "id": str(s.id),
        "health_score": s.health_score,
        "total_value": s.portfolio_snapshot.total_value if s.portfolio_snapshot else None,
        "created_at": s.created_at.isoformat(),
    } for s in snapshots]


@router.post("/portfolios/{portfolio_id}/analytics/recompute")
def recompute_analytics(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)

    # Trigger Celery task
    from app.tasks.analytics_tasks import recompute_analytics as recompute_task
    task = recompute_task.delay(str(portfolio.id))

    log_event(db, current_user.id, "analytics_recompute", {
        "portfolio_id": str(portfolio.id),
        "task_id": task.id,
    }, portfolio_id=portfolio.id)

    return {"task_id": task.id, "status": "queued"}
