import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.warning import Warning as WarningModel
from app.schemas.warning import WarningResponse
from app.services.portfolio_service import get_portfolio
from app.services.warning_service import get_latest_warnings

router = APIRouter(tags=["warnings"])


@router.get("/portfolios/{portfolio_id}/warnings", response_model=list[WarningResponse])
def list_warnings(
    portfolio_id: uuid.UUID,
    severity: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    warnings = get_latest_warnings(db, portfolio.id)
    if severity:
        warnings = [w for w in warnings if w.severity == severity]
    return [WarningResponse(
        id=str(w.id), warning_type=w.warning_type, severity=w.severity,
        title=w.title, description=w.description, evidence_json=w.evidence_json,
        triggered_at=w.triggered_at,
    ) for w in warnings]


@router.get("/portfolios/{portfolio_id}/warnings/latest", response_model=list[WarningResponse])
def get_latest(
    portfolio_id: uuid.UUID,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    warnings = get_latest_warnings(db, portfolio.id)[:limit]
    return [WarningResponse(
        id=str(w.id), warning_type=w.warning_type, severity=w.severity,
        title=w.title, description=w.description, evidence_json=w.evidence_json,
        triggered_at=w.triggered_at,
    ) for w in warnings]
