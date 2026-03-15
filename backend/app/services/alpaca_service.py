"""Alpaca API integration for fetching portfolio positions."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError
from app.services.name_resolver import resolve_stock_names


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

    symbols_to_resolve = []
    position_rows = []

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

            symbols_to_resolve.append(symbol)
            position_rows.append({
                "symbol": symbol,
                "qty": qty,
                "avg_price": avg_price,
                "cost_basis": float(pos.get("cost_basis", 0)) or avg_price * qty,
                "asset_type": "equity" if asset_class == "us_equity" else asset_class,
            })
        except (ValueError, KeyError) as e:
            errors.append(f"Position {pos.get('symbol', '?')}: {str(e)}")
            skipped += 1

    name_map = resolve_stock_names(db, symbols_to_resolve)

    for row in position_rows:
        symbol = row["symbol"]
        position = Position(
            account_id=account.id,
            symbol=symbol,
            asset_name=name_map.get(symbol.upper(), symbol),
            asset_type=row["asset_type"],
            quantity=row["qty"],
            cost_basis_per_share=row["avg_price"],
            cost_basis_total=row["cost_basis"],
            currency="USD",
        )
        db.add(position)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
