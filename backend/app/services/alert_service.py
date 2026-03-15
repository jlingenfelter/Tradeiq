import uuid

from sqlalchemy.orm import Session

from app.models.alert import AlertSubscription
from app.core.exceptions import NotFoundError


def list_alerts(db: Session, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> list[AlertSubscription]:
    return (
        db.query(AlertSubscription)
        .filter(
            AlertSubscription.portfolio_id == portfolio_id,
            AlertSubscription.user_id == user_id,
        )
        .all()
    )


def create_alert(
    db: Session,
    user_id: uuid.UUID,
    portfolio_id: uuid.UUID,
    alert_type: str,
    threshold_json: dict,
    channel: str = "in_app",
    enabled: bool = True,
) -> AlertSubscription:
    alert = AlertSubscription(
        user_id=user_id,
        portfolio_id=portfolio_id,
        alert_type=alert_type,
        threshold_json=threshold_json,
        channel=channel,
        enabled=enabled,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def update_alert(
    db: Session,
    alert_id: uuid.UUID,
    user_id: uuid.UUID,
    threshold_json: dict | None = None,
    channel: str | None = None,
    enabled: bool | None = None,
) -> AlertSubscription:
    alert = db.query(AlertSubscription).filter(
        AlertSubscription.id == alert_id,
        AlertSubscription.user_id == user_id,
    ).first()
    if not alert:
        raise NotFoundError("Alert subscription not found")

    if threshold_json is not None:
        alert.threshold_json = threshold_json
    if channel is not None:
        alert.channel = channel
    if enabled is not None:
        alert.enabled = enabled

    db.commit()
    db.refresh(alert)
    return alert


def delete_alert(db: Session, alert_id: uuid.UUID, user_id: uuid.UUID) -> None:
    alert = db.query(AlertSubscription).filter(
        AlertSubscription.id == alert_id,
        AlertSubscription.user_id == user_id,
    ).first()
    if not alert:
        raise NotFoundError("Alert subscription not found")
    db.delete(alert)
    db.commit()
