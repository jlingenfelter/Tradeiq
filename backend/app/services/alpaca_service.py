"""Alpaca API integration for fetching portfolio positions."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


ALPACA_LIVE_URL = "https://api.alpaca.markets"
ALPACA_PAPER_URL = "https://paper-api.alpaca.markets"


def _get_headers(api_key: str, api_secret: str) -> dict:
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
    }


def fetch_alpaca_account(api_key: str, api_secret: str, environment: str = "live") -> dict:
    """Fetch account info from Alpaca."""
    base_url = ALPACA_LIVE_URL if environment == "live" else ALPACA_PAPER_URL

    try:
        resp = httpx.get(
            f"{base_url}/v2/account",
            headers=_get_headers(api_key, api_secret),
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Alpaca: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("Invalid Alpaca API credentials")
    if resp.status_code == 403:
        raise BadRequestError("Alpaca API key does not have required permissions")
    if resp.status_code != 200:
        raise BadRequestError(f"Alpaca API error: {resp.status_code}")

    return resp.json()


def fetch_alpaca_positions(api_key: str, api_secret: str, environment: str = "live") -> list[dict]:
    """Fetch all open positions from Alpaca."""
    base_url = ALPACA_LIVE_URL if environment == "live" else ALPACA_PAPER_URL

    try:
        resp = httpx.get(
            f"{base_url}/v2/positions",
            headers=_get_headers(api_key, api_secret),
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Alpaca: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("Invalid Alpaca API credentials")
    if resp.status_code != 200:
        raise BadRequestError(f"Alpaca API error: {resp.status_code}")

    return resp.json()


def import_alpaca_positions(
    db: Session,
    portfolio: Portfolio,
    api_key: str,
    api_secret: str,
    environment: str = "live",
) -> dict:
    """Import all positions from Alpaca into a portfolio."""
    positions_data = fetch_alpaca_positions(api_key, api_secret, environment)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "alpaca",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="Alpaca",
            source_type="alpaca",
        )
        db.add(account)
        db.flush()

    # Clear existing positions for a fresh sync
    db.query(Position).filter(Position.account_id == account.id).delete()

    imported = 0
    skipped = 0
    errors = []

    for pos in positions_data:
        try:
            symbol = pos.get("symbol", "")
            if not symbol:
                skipped += 1
                continue

            qty = float(pos.get("qty", 0))
            if qty <= 0:
                skipped += 1
                continue

            avg_price = float(pos.get("avg_entry_price", 0))
            asset_class = pos.get("asset_class", "us_equity")

            position = Position(
                account_id=account.id,
                symbol=symbol,
                asset_name=pos.get("symbol", symbol),
                asset_type="equity" if asset_class == "us_equity" else asset_class,
                quantity=qty,
                cost_basis_per_share=avg_price,
                cost_basis_total=float(pos.get("cost_basis", 0)) or avg_price * qty,
                currency="USD",
            )
            db.add(position)
            imported += 1
        except (ValueError, KeyError) as e:
            errors.append(f"Position {pos.get('symbol', '?')}: {str(e)}")
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
