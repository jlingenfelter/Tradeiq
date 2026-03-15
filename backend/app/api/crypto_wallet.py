import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.portfolio_service import get_portfolio
from app.services.crypto_wallet_service import (
    validate_wallet_address,
    fetch_wallet_holdings,
    import_wallet_positions,
)
from app.services.analytics_service import compute_portfolio_analytics

router = APIRouter(prefix="/crypto-wallet", tags=["crypto-wallet"])


class WalletTestRequest(BaseModel):
    address: str


class WalletTestResponse(BaseModel):
    success: bool
    chain: str | None = None
    token_count: int = 0
    message: str = ""


class WalletSyncRequest(BaseModel):
    address: str
    portfolio_id: str


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
    chain: str | None = None


@router.post("/test", response_model=WalletTestResponse)
def test_wallet(
    body: WalletTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Validate wallet address and preview holdings."""
    try:
        validate_wallet_address(body.address)
        chain, holdings = fetch_wallet_holdings(body.address)
        return WalletTestResponse(
            success=True,
            chain=chain,
            token_count=len(holdings),
            message=f"Found {len(holdings)} token(s) on {chain.capitalize()}",
        )
    except Exception as e:
        return WalletTestResponse(success=False, message=str(e))


@router.post("/sync", response_model=SyncResponse)
def sync_wallet(
    body: WalletSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Import crypto holdings from a wallet into a portfolio."""
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_wallet_positions(db, portfolio, body.address)
    if result["imported"] > 0:
        try:
            compute_portfolio_analytics(db, body.portfolio_id)
        except Exception:
            pass
    return SyncResponse(**result)
