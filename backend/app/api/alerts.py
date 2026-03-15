import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse
from app.services.portfolio_service import get_portfolio
from app.services.alert_service import list_alerts, create_alert, update_alert, delete_alert

router = APIRouter(tags=["alerts"])


@router.get("/portfolios/{portfolio_id}/alerts", response_model=list[AlertResponse])
def get_alerts(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    alerts = list_alerts(db, portfolio.id, current_user.id)
    return [AlertResponse(
        id=str(a.id), portfolio_id=str(a.portfolio_id), alert_type=a.alert_type,
        threshold_json=a.threshold_json, channel=a.channel, enabled=a.enabled,
        created_at=a.created_at,
    ) for a in alerts]


@router.post("/portfolios/{portfolio_id}/alerts", response_model=AlertResponse)
def create_new_alert(
    portfolio_id: uuid.UUID,
    body: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    alert = create_alert(
        db, current_user.id, portfolio.id,
        body.alert_type, body.threshold_json, body.channel, body.enabled,
    )
    return AlertResponse(
        id=str(alert.id), portfolio_id=str(alert.portfolio_id), alert_type=alert.alert_type,
        threshold_json=alert.threshold_json, channel=alert.channel, enabled=alert.enabled,
        created_at=alert.created_at,
    )


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
def update_existing_alert(
    alert_id: uuid.UUID,
    body: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = update_alert(db, alert_id, current_user.id, body.threshold_json, body.channel, body.enabled)
    return AlertResponse(
        id=str(alert.id), portfolio_id=str(alert.portfolio_id), alert_type=alert.alert_type,
        threshold_json=alert.threshold_json, channel=alert.channel, enabled=alert.enabled,
        created_at=alert.created_at,
    )


@router.delete("/alerts/{alert_id}")
def delete_existing_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_alert(db, alert_id, current_user.id)
    return {"message": "Alert deleted"}
