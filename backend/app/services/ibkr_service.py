"""Interactive Brokers Client Portal API integration for fetching portfolio positions."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


# IBKR Client Portal API runs on localhost by default (requires IB Gateway)
# Users provide the gateway URL where their IBKR Client Portal API is running
IBKR_DEFAULT_URL = "https://localhost:5000"


def _get_base_url(gateway_url: str | None) -> str:
    return (gateway_url or IBKR_DEFAULT_URL).rstrip("/")


def fetch_ibkr_accounts(gateway_url: str | None = None) -> list[dict]:
    """Fetch account list from IBKR Client Portal API."""
    base_url = _get_base_url(gateway_url)

    try:
        resp = httpx.get(
            f"{base_url}/v1/api/iserver/accounts",
            timeout=30,
            verify=False,  # IBKR Client Portal uses self-signed certs
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to IBKR Gateway: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("IBKR session not authenticated. Please log in to IB Gateway.")
    if resp.status_code != 200:
        raise BadRequestError(f"IBKR API error: {resp.status_code}")

    data = resp.json()
    return data.get("accounts", [])


def fetch_ibkr_positions(account_id: str, gateway_url: str | None = None) -> list[dict]:
    """Fetch positions for an IBKR account."""
    base_url = _get_base_url(gateway_url)

    try:
        resp = httpx.get(
            f"{base_url}/v1/api/portfolio/{account_id}/positions/0",
            timeout=30,
            verify=False,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to IBKR Gateway: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("IBKR session expired. Please re-authenticate in IB Gateway.")
    if resp.status_code != 200:
        raise BadRequestError(f"IBKR API error: {resp.status_code}")

    return resp.json()


def import_ibkr_positions(
    db: Session,
    portfolio: Portfolio,
    ibkr_account_id: str,
    gateway_url: str | None = None,
) -> dict:
    """Import positions from IBKR into a portfolio."""
    positions_data = fetch_ibkr_positions(ibkr_account_id, gateway_url)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "ibkr",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="Interactive Brokers",
            source_type="ibkr",
            external_account_id=ibkr_account_id,
        )
        db.add(account)
        db.flush()

    db.query(Position).filter(Position.account_id == account.id).delete()

    imported = 0
    skipped = 0
    errors = []

    for pos in positions_data:
        try:
            ticker = pos.get("ticker", "") or pos.get("contractDesc", "")
            if not ticker:
                skipped += 1
                continue

            qty = float(pos.get("position", 0))
            if qty == 0:
                skipped += 1
                continue

            avg_cost = float(pos.get("avgCost", 0))
            mkt_value = float(pos.get("mktValue", 0))
            asset_class = pos.get("assetClass", "STK")

            asset_type_map = {
                "STK": "equity",
                "OPT": "option",
                "FUT": "future",
                "CASH": "forex",
                "BOND": "bond",
                "FOP": "future_option",
                "WAR": "warrant",
            }

            position = Position(
                account_id=account.id,
                symbol=ticker,
                asset_name=pos.get("contractDesc", ticker),
                asset_type=asset_type_map.get(asset_class, "equity"),
                quantity=abs(qty),
                cost_basis_per_share=avg_cost,
                cost_basis_total=avg_cost * abs(qty) if avg_cost else None,
                currency=pos.get("currency", "USD"),
            )
            db.add(position)
            imported += 1
        except (ValueError, KeyError) as e:
            errors.append(f"Position {pos.get('ticker', '?')}: {str(e)}")
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
