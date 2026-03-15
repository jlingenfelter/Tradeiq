"""Trading 212 API integration for fetching portfolio positions."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


T212_LIVE_URL = "https://live.trading212.com/api/v0"
T212_DEMO_URL = "https://demo.trading212.com/api/v0"


def _get_headers(api_key: str) -> dict:
    return {
        "Authorization": api_key,
    }


def fetch_t212_positions(api_key: str, environment: str = "live") -> list[dict]:
    """Fetch all open positions from Trading 212 API."""
    base_url = T212_LIVE_URL if environment == "live" else T212_DEMO_URL

    try:
        resp = httpx.get(
            f"{base_url}/equity/portfolio",
            headers=_get_headers(api_key),
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Trading 212: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("Invalid Trading 212 API key")
    if resp.status_code == 403:
        raise BadRequestError("Trading 212 API key does not have portfolio permissions")
    if resp.status_code != 200:
        raise BadRequestError(f"Trading 212 API error: {resp.status_code}")

    return resp.json()


def fetch_t212_account_info(api_key: str, environment: str = "live") -> dict:
    """Fetch account info from Trading 212."""
    base_url = T212_LIVE_URL if environment == "live" else T212_DEMO_URL

    try:
        resp = httpx.get(
            f"{base_url}/equity/account/info",
            headers=_get_headers(api_key),
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Trading 212: {str(e)}")

    if resp.status_code != 200:
        raise BadRequestError(f"Trading 212 API error: {resp.status_code}")

    return resp.json()


def import_t212_positions(
    db: Session,
    portfolio: Portfolio,
    api_key: str,
    environment: str = "live",
) -> dict:
    """Import all positions from Trading 212 into a portfolio."""
    positions_data = fetch_t212_positions(api_key, environment)

    # Create or find the Trading 212 account
    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "trading212",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="Trading 212",
            source_type="trading212",
        )
        db.add(account)
        db.flush()

    # Clear existing positions from this account to do a fresh sync
    db.query(Position).filter(Position.account_id == account.id).delete()

    imported = 0
    skipped = 0
    errors = []

    for pos in positions_data:
        try:
            ticker = pos.get("ticker", "")
            if not ticker:
                skipped += 1
                continue

            # Trading 212 tickers look like "AAPL_US_EQ" — extract the symbol
            symbol = ticker.split("_")[0] if "_" in ticker else ticker

            quantity = pos.get("quantity", 0)
            if not quantity or quantity <= 0:
                skipped += 1
                continue

            avg_price = pos.get("averagePrice", 0)
            current_price = pos.get("currentPrice", 0)
            ppl = pos.get("ppl", 0)  # profit/loss

            position = Position(
                account_id=account.id,
                symbol=symbol,
                asset_name=symbol,
                asset_type="equity",
                quantity=quantity,
                cost_basis_per_share=avg_price,
                cost_basis_total=avg_price * quantity if avg_price else None,
                currency="USD",
            )
            db.add(position)
            imported += 1
        except (ValueError, KeyError) as e:
            errors.append(f"Position {pos.get('ticker', '?')}: {str(e)}")
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
