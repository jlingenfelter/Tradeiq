from app.celery_app import celery_app
from app.database import SessionLocal


@celery_app.task(name="recompute_analytics")
def recompute_analytics(portfolio_id: str) -> dict:
    from app.services.analytics_service import compute_portfolio_analytics
    db = SessionLocal()
    try:
        result = compute_portfolio_analytics(db, portfolio_id)
        return {"portfolio_id": portfolio_id, "health_score": result.get("health_score")}
    finally:
        db.close()
