"""Kraken exchange integration — fetch spot balances using API key/secret."""

import hashlib
import hmac
import base64
import time
import urllib.parse

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


KRAKEN_BASE_URL = "https://api.kraken.com"

# Map Kraken's internal asset codes to standard symbols
KRAKEN_ASSET_MAP = {
    "XXBT": "BTC", "XBT": "BTC",
    "XETH": "ETH",
    "XXRP": "XRP",
    "XLTC": "LTC",
    "XXLM": "XLM",
    "XXDG": "DOGE", "XDG": "DOGE",
    "XZEC": "ZEC",
    "XXMR": "XMR",
    "XETC": "ETC",
    "XREP": "REP",
    "ZUSD": "USD",
    "ZEUR": "EUR",
    "ZGBP": "GBP",
    "ZJPY": "JPY",
    "ZCAD": "CAD",
    "ZAUD": "AUD",
}

# Fiat currencies to skip (we only want crypto)
FIAT_SYMBOLS = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "USDT", "USDC", "DAI"}


def _normalize_symbol(kraken_code: str) -> str:
    """Convert Kraken's internal codes to standard ticker symbols."""
    return KRAKEN_ASSET_MAP.get(kraken_code, kraken_code)


def _kraken_signature(url_path: str, data: dict, secret: str) -> str:
    """Generate Kraken API signature (HMAC-SHA512 of SHA256)."""
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data["nonce"]) + postdata).encode()
    message = url_path.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


def _private_request(endpoint: str, api_key: str, api_secret: str, data: dict | None = None) -> dict:
    """Make an authenticated request to Kraken's private API."""
    url_path = f"/0/private/{endpoint}"
    url = f"{KRAKEN_BASE_URL}{url_path}"

    if data is None:
        data = {}
    data["nonce"] = str(int(time.time() * 1000))

    try:
        sig = _kraken_signature(url_path, data, api_secret)
    except Exception as e:
        raise BadRequestError(f"Invalid Kraken API secret format: {str(e)}")

    headers = {
        "API-Key": api_key,
        "API-Sign": sig,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        resp = httpx.post(url, headers=headers, data=data, timeout=30)
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Kraken: {str(e)}")

    if resp.status_code != 200:
        raise BadRequestError(f"Kraken API error: {resp.status_code}")

    result = resp.json()
    errors = result.get("error", [])
    if errors:
        error_msg = "; ".join(str(e) for e in errors)
        if "EAPI:Invalid key" in error_msg:
            raise BadRequestError("Invalid Kraken API key")
        if "EAPI:Invalid signature" in error_msg:
            raise BadRequestError("Invalid Kraken API secret")
        if "EGeneral:Permission denied" in error_msg:
            raise BadRequestError("Kraken API key does not have 'Query Funds' permission")
        raise BadRequestError(f"Kraken API error: {error_msg}")

    return result.get("result", {})


def fetch_kraken_balance(api_key: str, api_secret: str) -> list[dict]:
    """Fetch all non-zero balances from Kraken."""
    balances = _private_request("Balance", api_key, api_secret)

    holdings = []
    for asset_code, balance_str in balances.items():
        balance = float(balance_str)
        if balance <= 0:
            continue

        symbol = _normalize_symbol(asset_code)

        # Skip fiat balances — wealth service tracks cash separately
        if symbol in FIAT_SYMBOLS:
            continue

        holdings.append({
            "symbol": symbol,
            "name": symbol,
            "quantity": balance,
            "asset_type": "crypto",
        })

    return holdings


def test_kraken_connection(api_key: str, api_secret: str) -> dict:
    """Test Kraken API credentials and return a summary."""
    holdings = fetch_kraken_balance(api_key, api_secret)
    return {
        "success": True,
        "token_count": len(holdings),
        "message": f"Connected — found {len(holdings)} crypto asset(s) on Kraken",
    }


def import_kraken_positions(
    db: Session,
    portfolio: Portfolio,
    api_key: str,
    api_secret: str,
) -> dict:
    """Import Kraken crypto holdings into a portfolio."""
    holdings = fetch_kraken_balance(api_key, api_secret)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "kraken",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="Kraken",
            source_type="kraken",
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
