"""Manage connected broker accounts and trigger re-syncs."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.portfolio import Account
from app.services.portfolio_service import get_portfolio
from app.services.sync_service import sync_account, sync_portfolio_accounts

router = APIRouter(tags=["connections"])


class ConnectionInfo(BaseModel):
    id: str
    portfolio_id: str
    name: str
    source_type: str
    environment: str | None
    auto_sync: bool
    last_synced_at: str | None
    sync_error: str | None
    position_count: int


class SyncResultResponse(BaseModel):
    account_id: str
    source_type: str
    name: str
    imported: int
    skipped: int
    errors: list[str]


@router.get("/portfolios/{portfolio_id}/connections", response_model=list[ConnectionInfo])
def list_connections(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all connected accounts for a portfolio."""
    portfolio = get_portfolio(db, portfolio_id, current_user)
    accounts = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type != "manual",
        Account.source_type != "csv",
    ).all()

    return [
        ConnectionInfo(
            id=str(a.id),
            portfolio_id=str(a.portfolio_id),
            name=a.name,
            source_type=a.source_type,
            environment=a.environment,
            auto_sync=a.auto_sync,
            last_synced_at=a.last_synced_at.isoformat() if a.last_synced_at else None,
            sync_error=a.sync_error,
            position_count=len(a.positions),
        )
        for a in accounts
    ]


@router.post("/portfolios/{portfolio_id}/connections/sync-all", response_model=list[SyncResultResponse])
def sync_all_connections(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-sync all connected accounts for a portfolio."""
    get_portfolio(db, portfolio_id, current_user)
    results = sync_portfolio_accounts(db, str(portfolio_id))
    return [SyncResultResponse(**r) for r in results]


@router.post("/connections/{account_id}/sync", response_model=SyncResultResponse)
def sync_single_connection(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-sync a single connected account."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Connection not found")
    # Verify ownership
    get_portfolio(db, account.portfolio_id, current_user)
    result = sync_account(db, account)
    return SyncResultResponse(
        account_id=str(account.id),
        source_type=account.source_type,
        name=account.name,
        imported=result.get("imported", 0),
        skipped=result.get("skipped", 0),
        errors=result.get("errors", []),
    )


@router.delete("/connections/{account_id}")
def disconnect_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect (remove credentials and disable auto-sync) for an account."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Connection not found")
    get_portfolio(db, account.portfolio_id, current_user)

    account.encrypted_credentials = None
    account.auto_sync = False
    account.sync_error = None
    db.commit()
    return {"status": "disconnected"}
