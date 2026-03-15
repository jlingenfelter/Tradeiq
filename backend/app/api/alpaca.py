import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.portfolio_service import get_portfolio
from app.services.alpaca_service import (
    fetch_alpaca_account,
    import_alpaca_positions,
)
from app.services.analytics_service import compute_portfolio_analytics

router = APIRouter(prefix="/alpaca", tags=["alpaca"])


class AlpacaTestRequest(BaseModel):
    api_key: str
    api_secret: str
    environment: str = "live"  # "live" or "paper"


class AlpacaTestResponse(BaseModel):
    success: bool
    account_id: str | None = None
    currency: str | None = None
    buying_power: str | None = None
    message: str = ""


class AlpacaSyncRequest(BaseModel):
    api_key: str
    api_secret: str
    portfolio_id: str
    environment: str = "live"


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/test", response_model=AlpacaTestResponse)
def test_connection(
    body: AlpacaTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Alpaca API key connection."""
    try:
        info = fetch_alpaca_account(body.api_key, body.api_secret, body.environment)
        return AlpacaTestResponse(
            success=True,
            account_id=info.get("account_number", ""),
            currency=info.get("currency", "USD"),
            buying_power=info.get("buying_power", ""),
            message="Connected successfully",
        )
    except Exception as e:
        return AlpacaTestResponse(success=False, message=str(e))


@router.post("/sync", response_model=SyncResponse)
def sync_positions(
    body: AlpacaSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync positions from Alpaca into a portfolio."""
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_alpaca_positions(db, portfolio, body.api_key, body.api_secret, body.environment)
    if result["imported"] > 0:
        try:
            compute_portfolio_analytics(db, body.portfolio_id)
        except Exception:
            pass
    return SyncResponse(**result)
