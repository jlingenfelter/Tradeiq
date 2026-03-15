import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.wealth import AlertSubscription as AlertModel
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/subscriptions", response_model=list[AlertResponse])
def list_alert_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.alert import AlertSubscription
    alerts = db.query(AlertSubscription).filter(
        AlertSubscription.user_id == current_user.id
    ).all()
    return [_to_response(a) for a in alerts]


@router.post("/subscriptions", response_model=AlertResponse)
def create_alert_subscription(
    body: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.alert import AlertSubscription
    alert = AlertSubscription(
        user_id=current_user.id,
        alert_type=body.alert_type,
        threshold_json=body.threshold_json or {},
        channel=body.channel,
        enabled=body.enabled,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _to_response(alert)


@router.patch("/subscriptions/{alert_id}", response_model=AlertResponse)
def update_alert_subscription(
    alert_id: uuid.UUID,
    body: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.alert import AlertSubscription
    alert = db.query(AlertSubscription).filter(
        AlertSubscription.id == alert_id,
        AlertSubscription.user_id == current_user.id,
    ).first()
    if not alert:
        raise NotFoundError("Alert subscription not found")
    if body.threshold_json is not None:
        alert.threshold_json = body.threshold_json
    if body.channel is not None:
        alert.channel = body.channel
    if body.enabled is not None:
        alert.enabled = body.enabled
    db.commit()
    db.refresh(alert)
    return _to_response(alert)


@router.delete("/subscriptions/{alert_id}")
def delete_alert_subscription(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.alert import AlertSubscription
    alert = db.query(AlertSubscription).filter(
        AlertSubscription.id == alert_id,
        AlertSubscription.user_id == current_user.id,
    ).first()
    if not alert:
        raise NotFoundError("Alert subscription not found")
    db.delete(alert)
    db.commit()
    return {"message": "Alert subscription deleted"}


def _to_response(a) -> AlertResponse:
    return AlertResponse(
        id=str(a.id),
        alert_type=a.alert_type,
        threshold_json=a.threshold_json,
        channel=a.channel,
        enabled=a.enabled,
        created_at=a.created_at,
    )
