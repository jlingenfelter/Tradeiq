import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.portfolio_service import get_portfolio
from app.services.moneybox_service import (
    test_moneybox_connection,
    import_moneybox_positions,
)
from app.models.portfolio import Account
from app.services.analytics_service import compute_portfolio_analytics
from app.services.sync_service import save_credentials

router = APIRouter(prefix="/moneybox", tags=["moneybox"])


class MoneyboxTestRequest(BaseModel):
    email: str
    password: str


class MoneyboxTestResponse(BaseModel):
    success: bool
    account_count: int = 0
    total_value: float = 0
    currency: str = "GBP"
    message: str = ""


class MoneyboxSyncRequest(BaseModel):
    email: str
    password: str
    portfolio_id: str


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/test", response_model=MoneyboxTestResponse)
def test_moneybox(
    body: MoneyboxTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Moneybox credentials and preview holdings."""
    try:
        result = test_moneybox_connection(body.email, body.password)
        return MoneyboxTestResponse(**result)
    except Exception as e:
        return MoneyboxTestResponse(success=False, message=str(e))


@router.post("/sync", response_model=SyncResponse)
def sync_moneybox(
    body: MoneyboxSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Import Moneybox holdings into a portfolio."""
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_moneybox_positions(db, portfolio, body.email, body.password)
    # Save credentials for auto-sync
    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "moneybox",
    ).first()
    if account:
        save_credentials(
            account,
            {"email": body.email, "password": body.password},
            "live",
            db,
        )
    if result["imported"] > 0:
        try:
            compute_portfolio_analytics(db, body.portfolio_id)
        except Exception:
            pass
    return SyncResponse(**result)
