"""Auto-sync service — refreshes positions for all connected accounts with saved credentials."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.portfolio import Account
from app.core.encryption import encrypt_value, decrypt_value
from app.services.analytics_service import compute_portfolio_analytics


def save_credentials(account: Account, credentials: dict, environment: str, db: Session):
    """Encrypt and save API credentials on an account for auto-sync."""
    account.encrypted_credentials = encrypt_value(json.dumps(credentials))
    account.environment = environment
    account.auto_sync = True
    account.last_synced_at = datetime.now(timezone.utc)
    account.sync_error = None
    db.flush()


def get_credentials(account: Account) -> dict:
    """Decrypt and return saved credentials for an account."""
    if not account.encrypted_credentials:
        return {}
    return json.loads(decrypt_value(account.encrypted_credentials))


def sync_account(db: Session, account: Account) -> dict:
    """Re-sync a single account using its saved credentials."""
    if not account.encrypted_credentials:
        return {"error": "No saved credentials"}

    creds = get_credentials(account)
    env = account.environment or "live"
    portfolio = account.portfolio
    result = {"imported": 0, "skipped": 0, "errors": []}

    try:
        if account.source_type == "trading212":
            from app.services.trading212_service import import_t212_positions
            result = import_t212_positions(
                db, portfolio,
                creds.get("api_key", ""), creds.get("api_secret", ""), env
            )
        elif account.source_type == "alpaca":
            from app.services.alpaca_service import import_alpaca_positions
            result = import_alpaca_positions(
                db, portfolio,
                creds.get("api_key", ""), creds.get("api_secret", ""), env
            )
        elif account.source_type == "ibkr":
            from app.services.ibkr_service import import_ibkr_positions
            result = import_ibkr_positions(
                db, portfolio,
                account.external_account_id or "", creds.get("gateway_url")
            )
        elif account.source_type == "ig":
            from app.services.ig_service import import_ig_positions
            result = import_ig_positions(
                db, portfolio,
                creds.get("api_key", ""), creds.get("access_token", ""),
                creds.get("cst", ""), env
            )
        elif account.source_type == "tradier":
            from app.services.tradier_service import import_tradier_positions
            result = import_tradier_positions(
                db, portfolio,
                creds.get("access_token", ""),
                account.external_account_id or "", env
            )
        elif account.source_type == "crypto_wallet":
            from app.services.crypto_wallet_service import import_wallet_positions
            result = import_wallet_positions(
                db, portfolio,
                account.external_account_id or ""
            )
        else:
            return {"error": f"Unknown source type: {account.source_type}"}

        account.last_synced_at = datetime.now(timezone.utc)
        account.sync_error = None
        db.flush()

    except Exception as e:
        account.sync_error = str(e)
        account.last_synced_at = datetime.now(timezone.utc)
        db.flush()
        result["errors"].append(str(e))

    return result


def sync_all_accounts(db: Session) -> list[dict]:
    """Sync all accounts that have auto_sync enabled and saved credentials."""
    accounts = db.query(Account).filter(
        Account.auto_sync == True,
        Account.encrypted_credentials.isnot(None),
    ).all()

    results = []
    for account in accounts:
        result = sync_account(db, account)
        results.append({
            "account_id": str(account.id),
            "portfolio_id": str(account.portfolio_id),
            "source_type": account.source_type,
            "name": account.name,
            **result,
        })

    # Recompute analytics for affected portfolios
    portfolio_ids = set(str(a.portfolio_id) for a in accounts)
    for pid in portfolio_ids:
        try:
            compute_portfolio_analytics(db, pid)
        except Exception:
            pass

    return results


def sync_portfolio_accounts(db: Session, portfolio_id: str) -> list[dict]:
    """Sync all connected accounts for a specific portfolio."""
    accounts = db.query(Account).filter(
        Account.portfolio_id == portfolio_id,
        Account.auto_sync == True,
        Account.encrypted_credentials.isnot(None),
    ).all()

    results = []
    for account in accounts:
        result = sync_account(db, account)
        results.append({
            "account_id": str(account.id),
            "source_type": account.source_type,
            "name": account.name,
            **result,
        })

    if accounts:
        try:
            compute_portfolio_analytics(db, portfolio_id)
        except Exception:
            pass

    return results
