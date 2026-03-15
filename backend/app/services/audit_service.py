import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_event(
    db: Session,
    user_id: uuid.UUID,
    event_type: str,
    payload: dict | None = None,
    portfolio_id: uuid.UUID | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        portfolio_id=portfolio_id,
        event_type=event_type,
        payload_json=payload or {},
    )
    db.add(entry)
    db.commit()
