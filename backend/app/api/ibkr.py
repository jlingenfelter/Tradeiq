import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.portfolio_service import get_portfolio
from app.services.ibkr_service import (
    fetch_ibkr_accounts,
    import_ibkr_positions,
)
from app.models.portfolio import Account
from app.services.analytics_service import compute_portfolio_analytics
from app.services.sync_service import save_credentials

router = APIRouter(prefix="/ibkr", tags=["ibkr"])


class IBKRTestRequest(BaseModel):
    gateway_url: str = "https://localhost:5000"


class IBKRTestResponse(BaseModel):
    success: bool
    accounts: list[str] = []
    message: str = ""


class IBKRSyncRequest(BaseModel):
    gateway_url: str = "https://localhost:5000"
    ibkr_account_id: str
    portfolio_id: str


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/test", response_model=IBKRTestResponse)
def test_connection(
    body: IBKRTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test IBKR Client Portal Gateway connection."""
    try:
        accounts = fetch_ibkr_accounts(body.gateway_url)
        return IBKRTestResponse(
            success=True,
            accounts=accounts,
            message=f"Connected — {len(accounts)} account(s) found",
        )
    except Exception as e:
        return IBKRTestResponse(success=False, message=str(e))


@router.post("/sync", response_model=SyncResponse)
def sync_positions(
    body: IBKRSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync positions from IBKR into a portfolio."""
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_ibkr_positions(db, portfolio, body.ibkr_account_id, body.gateway_url)
    account = db.query(Account).filter(Account.portfolio_id == portfolio.id, Account.source_type == "ibkr").first()
    if account:
        save_credentials(account, {"gateway_url": body.gateway_url}, "live", db)
    if result["imported"] > 0:
        try:
            compute_portfolio_analytics(db, body.portfolio_id)
        except Exception:
            pass
    return SyncResponse(**result)
