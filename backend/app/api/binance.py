import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.portfolio_service import get_portfolio
from app.services.binance_service import (
    test_binance_connection,
    import_binance_positions,
)
from app.models.portfolio import Account
from app.services.analytics_service import compute_portfolio_analytics
from app.services.sync_service import save_credentials

router = APIRouter(prefix="/binance", tags=["binance"])


class BinanceTestRequest(BaseModel):
    api_key: str
    api_secret: str


class BinanceTestResponse(BaseModel):
    success: bool
    token_count: int = 0
    message: str = ""


class BinanceSyncRequest(BaseModel):
    api_key: str
    api_secret: str
    portfolio_id: str


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/test", response_model=BinanceTestResponse)
def test_binance(
    body: BinanceTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Binance API credentials and preview balances."""
    try:
        result = test_binance_connection(body.api_key, body.api_secret)
        return BinanceTestResponse(**result)
    except Exception as e:
        return BinanceTestResponse(success=False, message=str(e))


@router.post("/sync", response_model=SyncResponse)
def sync_binance(
    body: BinanceSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Import Binance crypto holdings into a portfolio."""
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_binance_positions(db, portfolio, body.api_key, body.api_secret)
    # Save credentials for auto-sync
    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "binance",
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
