import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.portfolio_service import get_portfolio
from app.services.ig_service import (
    ig_authenticate,
    import_ig_positions,
)
from app.services.analytics_service import compute_portfolio_analytics

router = APIRouter(prefix="/ig", tags=["ig"])


class IGTestRequest(BaseModel):
    api_key: str
    username: str
    password: str
    environment: str = "live"


class IGTestResponse(BaseModel):
    success: bool
    account_id: str | None = None
    access_token: str | None = None
    cst: str | None = None
    message: str = ""


class IGSyncRequest(BaseModel):
    api_key: str
    access_token: str
    cst: str
    portfolio_id: str
    environment: str = "live"


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/test", response_model=IGTestResponse)
def test_connection(
    body: IGTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Authenticate with IG and return session tokens."""
    try:
        result = ig_authenticate(body.api_key, body.username, body.password, body.environment)
        return IGTestResponse(
            success=True,
            account_id=result.get("account_id", ""),
            access_token=result.get("access_token", ""),
            cst=result.get("cst", ""),
            message="Authenticated successfully",
        )
    except Exception as e:
        return IGTestResponse(success=False, message=str(e))


@router.post("/sync", response_model=SyncResponse)
def sync_positions(
    body: IGSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync positions from IG into a portfolio."""
    portfolio = get_portfolio(db, uuid.UUID(body.portfolio_id), current_user)
    result = import_ig_positions(
        db, portfolio, body.api_key, body.access_token, body.cst, body.environment
    )
    if result["imported"] > 0:
        try:
            compute_portfolio_analytics(db, body.portfolio_id)
        except Exception:
            pass
    return SyncResponse(**result)
