"""Tradier API integration for fetching portfolio positions."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError
from app.services.name_resolver import resolve_stock_names


TRADIER_LIVE_URL = "https://api.tradier.com"
TRADIER_SANDBOX_URL = "https://sandbox.tradier.com"


def _get_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }


def fetch_tradier_profile(access_token: str, environment: str = "live") -> dict:
    """Fetch user profile/account info from Tradier."""
    base_url = TRADIER_LIVE_URL if environment == "live" else TRADIER_SANDBOX_URL

    try:
        resp = httpx.get(
            f"{base_url}/v1/user/profile",
            headers=_get_headers(access_token),
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Tradier: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("Invalid Tradier access token")
    if resp.status_code != 200:
        raise BadRequestError(f"Tradier API error: {resp.status_code}")

    return resp.json()


def fetch_tradier_positions(access_token: str, account_id: str, environment: str = "live") -> list[dict]:
    """Fetch positions for a Tradier account."""
    base_url = TRADIER_LIVE_URL if environment == "live" else TRADIER_SANDBOX_URL

    try:
        resp = httpx.get(
            f"{base_url}/v1/accounts/{account_id}/positions",
            headers=_get_headers(access_token),
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Tradier: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("Invalid Tradier access token")
    if resp.status_code != 200:
        raise BadRequestError(f"Tradier API error: {resp.status_code}")

    data = resp.json()
    positions = data.get("positions", {})
    if positions == "null" or not positions:
        return []
    pos_list = positions.get("position", [])
    # Tradier returns a single object if only one position, not a list
    if isinstance(pos_list, dict):
        pos_list = [pos_list]
    return pos_list


def import_tradier_positions(
    db: Session,
    portfolio: Portfolio,
    access_token: str,
    tradier_account_id: str,
    environment: str = "live",
) -> dict:
    """Import positions from Tradier into a portfolio."""
    positions_data = fetch_tradier_positions(access_token, tradier_account_id, environment)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "tradier",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="Tradier",
            source_type="tradier",
            external_account_id=tradier_account_id,
        )
        db.add(account)
        db.flush()

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

            qty = float(pos.get("quantity", 0))
            if qty == 0:
                skipped += 1
                continue

            cost_basis = float(pos.get("cost_basis", 0))
            avg_price = cost_basis / abs(qty) if qty != 0 and cost_basis else 0

            symbols_to_resolve.append(symbol)
            position_rows.append({
                "symbol": symbol,
                "qty": abs(qty),
                "avg_price": avg_price,
                "cost_basis": cost_basis,
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
            asset_type="equity",
            quantity=row["qty"],
            cost_basis_per_share=row["avg_price"],
            cost_basis_total=row["cost_basis"] if row["cost_basis"] else None,
            currency="USD",
        )
        db.add(position)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
