import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tier_gate import require_pro
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.plaid import PlaidItem, PlaidAccount
from app.services.plaid_service import (
    create_link_token,
    exchange_public_token,
    sync_item_accounts,
    map_plaid_to_wealth,
)

router = APIRouter(prefix="/plaid", tags=["plaid"])


class ExchangeRequest(BaseModel):
    public_token: str
    metadata: dict = {}


# ── POST /plaid/link-token ──────────────────────────────────────────────
@router.post("/link-token")
def post_link_token(
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Create a Plaid Link token for the frontend."""
    token = create_link_token(db, current_user)
    return {"link_token": token}


# ── POST /plaid/exchange ────────────────────────────────────────────────
@router.post("/exchange")
def post_exchange(
    body: ExchangeRequest,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Exchange a Plaid public_token for an access_token and sync accounts."""
    result = exchange_public_token(db, current_user, body.public_token, body.metadata)
    return result


# ── POST /plaid/sync/{item_id} ──────────────────────────────────────────
@router.post("/sync/{item_id}")
def post_sync(
    item_id: uuid.UUID,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Re-sync accounts for a Plaid Item."""
    plaid_item = db.query(PlaidItem).filter(
        PlaidItem.id == item_id,
        PlaidItem.user_id == current_user.id,
    ).first()
    if not plaid_item:
        raise NotFoundError("Plaid item not found")

    accounts = sync_item_accounts(db, plaid_item)
    return {"accounts": accounts}


# ── GET /plaid/items ────────────────────────────────────────────────────
@router.get("/items")
def get_items(
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """List all Plaid items (linked institutions) for the user."""
    items = db.query(PlaidItem).filter(
        PlaidItem.user_id == current_user.id,
    ).order_by(PlaidItem.created_at.desc()).all()

    results = []
    for item in items:
        accounts = db.query(PlaidAccount).filter(
            PlaidAccount.plaid_item_id == item.id,
        ).all()
        results.append({
            "id": str(item.id),
            "institution_name": item.institution_name,
            "status": item.status,
            "error_code": item.error_code,
            "consent_expiration": item.consent_expiration.isoformat() if item.consent_expiration else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "accounts": [
                {
                    "id": str(a.id),
                    "name": a.name,
                    "account_type": a.account_type,
                    "account_subtype": a.account_subtype,
                    "current_balance": a.current_balance,
                    "currency": a.currency,
                    "last_synced_at": a.last_synced_at.isoformat() if a.last_synced_at else None,
                }
                for a in accounts
            ],
        })

    return {"items": results}


# ── DELETE /plaid/items/{item_id} ───────────────────────────────────────
@router.delete("/items/{item_id}")
def delete_item(
    item_id: uuid.UUID,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Remove a linked Plaid item and its accounts."""
    plaid_item = db.query(PlaidItem).filter(
        PlaidItem.id == item_id,
        PlaidItem.user_id == current_user.id,
    ).first()
    if not plaid_item:
        raise NotFoundError("Plaid item not found")

    db.delete(plaid_item)  # cascade deletes accounts
    db.commit()
    return {"message": "Plaid item removed"}
