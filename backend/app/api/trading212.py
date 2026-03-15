import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.portfolio import Account
from app.services.portfolio_service import get_portfolio
from app.services.trading212_service import (
    fetch_t212_account_info,
    import_t212_positions,
)
from app.services.analytics_service import compute_portfolio_analytics
from app.services.sync_service import save_credentials

router = APIRouter(prefix="/trading212", tags=["trading212"])


class T212ConnectRequest(BaseModel):
    api_key: str
    api_secret: str
    portfolio_id: str
    environment: str = "live"


class T212SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


class T212TestRequest(BaseModel):
    api_key: str
    api_secret: str
    environment: str = "live"


class T212TestResponse(BaseModel):
    success: bool
    account_id: str | None = None
    currency: str | None = None
    message: str = ""


@router.post("/test", response_model=T212TestResponse)
def test_connection(
    body: T212TestRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        info = fetch_t212_account_info(body.api_key, body.api_secret, body.environment)
        return T212TestResponse(
            success=True,
            account_id=str(info.get("id", "")),
            currency=info.get("currencyCode", ""),
            message="Connected successfully",
        )
    except Exception as e:
        return T212TestResponse(success=False, message=str(e))


@router.post("/sync", response_model=T212SyncResponse)
def sync_positions(
    body: T212ConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_t212_positions(db, portfolio, body.api_key, body.api_secret, body.environment)

    # Save credentials for auto-sync
    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "trading212",
    ).first()
    if account:
        save_credentials(account, {"api_key": body.api_key, "api_secret": body.api_secret}, body.environment, db)

    if result["imported"] > 0:
        try:
            compute_portfolio_analytics(db, body.portfolio_id)
        except Exception:
            pass
    return T212SyncResponse(**result)
