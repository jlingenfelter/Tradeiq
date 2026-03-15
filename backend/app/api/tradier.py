import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.portfolio_service import get_portfolio
from app.services.tradier_service import (
    fetch_tradier_profile,
    import_tradier_positions,
)

router = APIRouter(prefix="/tradier", tags=["tradier"])


class TradierTestRequest(BaseModel):
    access_token: str
    environment: str = "live"


class TradierTestResponse(BaseModel):
    success: bool
    account_id: str | None = None
    name: str | None = None
    message: str = ""


class TradierSyncRequest(BaseModel):
    access_token: str
    tradier_account_id: str
    portfolio_id: str
    environment: str = "live"


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/test", response_model=TradierTestResponse)
def test_connection(
    body: TradierTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Tradier access token."""
    try:
        profile = fetch_tradier_profile(body.access_token, body.environment)
        account = profile.get("profile", {}).get("account", {})
        # Tradier can return a list of accounts
        if isinstance(account, list):
            account = account[0] if account else {}
        return TradierTestResponse(
            success=True,
            account_id=account.get("account_number", ""),
            name=account.get("classification", ""),
            message="Connected successfully",
        )
    except Exception as e:
        return TradierTestResponse(success=False, message=str(e))


@router.post("/sync", response_model=SyncResponse)
def sync_positions(
    body: TradierSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync positions from Tradier into a portfolio."""
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_tradier_positions(
        db, portfolio, body.access_token, body.tradier_account_id, body.environment
    )
    return SyncResponse(**result)
