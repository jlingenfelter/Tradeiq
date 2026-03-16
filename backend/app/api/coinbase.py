import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.portfolio_service import get_portfolio
from app.services.coinbase_service import (
    test_coinbase_connection,
    import_coinbase_positions,
)
from app.models.portfolio import Account
from app.services.analytics_service import compute_portfolio_analytics
from app.services.sync_service import save_credentials

router = APIRouter(prefix="/coinbase", tags=["coinbase"])


class CoinbaseTestRequest(BaseModel):
    api_key: str
    api_secret: str


class CoinbaseTestResponse(BaseModel):
    success: bool
    token_count: int = 0
    message: str = ""


class CoinbaseSyncRequest(BaseModel):
    api_key: str
    api_secret: str
    portfolio_id: str


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/test", response_model=CoinbaseTestResponse)
def test_coinbase(
    body: CoinbaseTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Coinbase API credentials and preview balances."""
    try:
        result = test_coinbase_connection(body.api_key, body.api_secret)
        return CoinbaseTestResponse(**result)
    except Exception as e:
        return CoinbaseTestResponse(success=False, message=str(e))


@router.post("/sync", response_model=SyncResponse)
def sync_coinbase(
    body: CoinbaseSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Import Coinbase crypto holdings into a portfolio."""
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_coinbase_positions(db, portfolio, body.api_key, body.api_secret)
    # Save credentials for auto-sync
    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "coinbase",
    ).first()
    if account:
        save_credentials(
            account,
            {"api_key": body.api_key, "api_secret": body.api_secret},
            "live",
            db,
        )
    if result["imported"] > 0:
        try:
            compute_portfolio_analytics(db, body.portfolio_id)
        except Exception:
            pass
    return SyncResponse(**result)
