import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tier_gate import require_pro
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.plaid import PlaidItem, PlaidAccount
from app.services.truelayer_service import (
    create_auth_url,
    exchange_code,
    sync_accounts,
)

router = APIRouter(prefix="/truelayer", tags=["truelayer"])


class CallbackRequest(BaseModel):
    code: str


# ── GET /truelayer/auth-url ─────────────────────────────────────────────
@router.get("/auth-url")
def get_auth_url(
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Generate the TrueLayer OAuth URL."""
    url = create_auth_url(db, current_user)
    return {"url": url}


# ── POST /truelayer/callback ────────────────────────────────────────────
@router.post("/callback")
async def post_callback(
    body: CallbackRequest,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Exchange the TrueLayer auth code for tokens."""
    result = await exchange_code(db, current_user, body.code)
    return result


# ── GET /truelayer/accounts ──────────────────────────────────────────────
@router.get("/accounts")
def get_accounts(
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """List all TrueLayer-linked accounts for the user."""
    # TrueLayer items have plaid_item_id starting with "truelayer_"
    items = db.query(PlaidItem).filter(
        PlaidItem.user_id == current_user.id,
        PlaidItem.plaid_item_id.like("truelayer_%"),
    ).all()

    accounts = []
    for item in items:
        item_accounts = db.query(PlaidAccount).filter(
            PlaidAccount.plaid_item_id == item.id,
        ).all()
        for a in item_accounts:
            accounts.append({
                "id": str(a.id),
                "name": a.name,
                "official_name": a.official_name,
                "account_type": a.account_type,
                "account_subtype": a.account_subtype,
                "current_balance": a.current_balance,
                "currency": a.currency,
                "last_synced_at": a.last_synced_at.isoformat() if a.last_synced_at else None,
            })

    return {"accounts": accounts}


# ── POST /truelayer/sync ────────────────────────────────────────────────
@router.post("/sync")
async def post_sync(
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Re-sync all TrueLayer accounts for the user."""
    items = db.query(PlaidItem).filter(
        PlaidItem.user_id == current_user.id,
        PlaidItem.plaid_item_id.like("truelayer_%"),
    ).all()

    all_accounts = []
    for item in items:
        try:
            synced = await sync_accounts(db, current_user, item.plaid_access_token)
            all_accounts.extend(synced)
        except Exception as e:
            item.status = "error"
            item.error_code = str(e)[:100]
            db.commit()

    return {"accounts": all_accounts, "synced_count": len(all_accounts)}
