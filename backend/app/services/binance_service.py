"""Binance exchange integration — fetch spot balances using API key/secret."""

import hashlib
import hmac
import time

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


BINANCE_BASE_URL = "https://api.binance.com"

# Fiat currencies to skip (we only want crypto holdings)
# Keep USDT and USDC as they are crypto stablecoins
FIAT_SYMBOLS = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "BRL", "TRY", "NGN", "ARS", "RUB"}


def _binance_signature(query_string: str, api_secret: str) -> str:
    """Generate HMAC-SHA256 signature for Binance API."""
    return hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _signed_request(endpoint: str, api_key: str, api_secret: str) -> dict:
    """Make an authenticated GET request to Binance API."""
    url = f"{BINANCE_BASE_URL}{endpoint}"

    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}&recvWindow=60000"

    try:
        signature = _binance_signature(query_string, api_secret)
    except Exception as e:
        raise BadRequestError(f"Invalid Binance API secret format: {str(e)}")

    query_string += f"&signature={signature}"

    headers = {
        "X-MBX-APIKEY": api_key,
    }

    try:
        resp = httpx.get(f"{url}?{query_string}", headers=headers, timeout=30)
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Binance: {str(e)}")

    if resp.status_code != 200:
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        code = body.get("code", resp.status_code)
        msg = body.get("msg", "Unknown error")

        if code == -2015 or "Invalid API-key" in msg:
            raise BadRequestError("Invalid Binance API key")
        if code == -1022 or "Signature" in msg:
            raise BadRequestError("Invalid Binance API secret")
        if code == -2014:
            raise BadRequestError("Invalid Binance API key")
        raise BadRequestError(f"Binance API error ({code}): {msg}")

    return resp.json()


def fetch_binance_balance(api_key: str, api_secret: str) -> list[dict]:
    """Fetch all non-zero balances from Binance."""
    data = _signed_request("/api/v3/account", api_key, api_secret)

    balances = data.get("balances", [])
    holdings = []

    for item in balances:
        asset = item.get("asset", "")
        free = float(item.get("free", "0"))
        locked = float(item.get("locked", "0"))
        total = free + locked

        if total <= 0:
            continue

        # Skip fiat currencies
        if asset in FIAT_SYMBOLS:
            continue

        holdings.append({
            "symbol": asset,
            "name": asset,
            "quantity": total,
            "asset_type": "crypto",
        })

    return holdings


def test_binance_connection(api_key: str, api_secret: str) -> dict:
    """Test Binance API credentials and return a summary."""
    holdings = fetch_binance_balance(api_key, api_secret)
    return {
        "success": True,
        "token_count": len(holdings),
        "message": f"Connected — found {len(holdings)} crypto asset(s) on Binance",
    }


def import_binance_positions(
    db: Session,
    portfolio: Portfolio,
    api_key: str,
    api_secret: str,
) -> dict:
    """Import Binance crypto holdings into a portfolio."""
    holdings = fetch_binance_balance(api_key, api_secret)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "binance",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="Binance",
            source_type="binance",
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
