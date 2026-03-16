"""Coinbase Advanced Trade API (v3) integration — fetch spot balances using API key/secret."""

import hashlib
import hmac
import time

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


COINBASE_BASE_URL = "https://api.coinbase.com"

# Fiat currencies to skip (we only want crypto)
FIAT_SYMBOLS = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "USDT", "USDC", "DAI"}


def _coinbase_signature(timestamp: str, method: str, path: str, body: str, api_secret: str) -> str:
    """Generate Coinbase Advanced Trade HMAC-SHA256 signature."""
    message = timestamp + method.upper() + path + body
    signature = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return signature


def _authenticated_request(
    method: str,
    path: str,
    api_key: str,
    api_secret: str,
    body: str = "",
) -> dict:
    """Make an authenticated request to the Coinbase Advanced Trade API."""
    url = f"{COINBASE_BASE_URL}{path}"
    timestamp = str(int(time.time()))

    try:
        sig = _coinbase_signature(timestamp, method, path, body, api_secret)
    except Exception as e:
        raise BadRequestError(f"Invalid Coinbase API secret format: {str(e)}")

    headers = {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": sig,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json",
    }

    try:
        if method.upper() == "GET":
            resp = httpx.get(url, headers=headers, timeout=30)
        else:
            resp = httpx.post(url, headers=headers, content=body, timeout=30)
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Coinbase: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("Invalid Coinbase API credentials")
    if resp.status_code == 403:
        raise BadRequestError("Coinbase API key does not have sufficient permissions")
    if resp.status_code != 200:
        raise BadRequestError(f"Coinbase API error: {resp.status_code}")

    return resp.json()


def fetch_coinbase_balance(api_key: str, api_secret: str) -> list[dict]:
    """Fetch all non-zero crypto balances from Coinbase."""
    accounts = []
    cursor = None

    # Paginate through all accounts
    while True:
        path = "/api/v3/brokerage/accounts"
        if cursor:
            path += f"?cursor={cursor}"

        result = _authenticated_request("GET", path, api_key, api_secret)

        for acct in result.get("accounts", []):
            balance = float(acct.get("available_balance", {}).get("value", "0"))
            hold = float(acct.get("hold", {}).get("value", "0"))
            total = balance + hold

            if total <= 0:
                continue

            symbol = acct.get("currency", "").upper()

            # Skip fiat balances
            if symbol in FIAT_SYMBOLS:
                continue

            accounts.append({
                "symbol": symbol,
                "name": acct.get("name", symbol),
                "quantity": total,
                "asset_type": "crypto",
            })

        # Check for next page
        next_cursor = result.get("cursor")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor

    return accounts


def test_coinbase_connection(api_key: str, api_secret: str) -> dict:
    """Test Coinbase API credentials and return a summary."""
    holdings = fetch_coinbase_balance(api_key, api_secret)
    return {
        "success": True,
        "token_count": len(holdings),
        "message": f"Connected — found {len(holdings)} crypto asset(s) on Coinbase",
    }


def import_coinbase_positions(
    db: Session,
    portfolio: Portfolio,
    api_key: str,
    api_secret: str,
) -> dict:
    """Import Coinbase crypto holdings into a portfolio."""
    holdings = fetch_coinbase_balance(api_key, api_secret)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "coinbase",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="Coinbase",
            source_type="coinbase",
        )
        db.add(account)
        db.flush()

    # Clear existing positions for a fresh sync
    db.query(Position).filter(Position.account_id == account.id).delete()

    imported = 0
    skipped = 0
    errors = []

    for h in holdings:
        try:
            symbol = h["symbol"]
            qty = h["quantity"]
            if not symbol or qty <= 0:
                skipped += 1
                continue

            position = Position(
                account_id=account.id,
                symbol=symbol,
                asset_name=h.get("name", symbol),
                asset_type="crypto",
                quantity=qty,
                currency="USD",
            )
            db.add(position)
            imported += 1
        except (ValueError, KeyError) as e:
            errors.append(f"{h.get('symbol', '?')}: {str(e)}")
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
