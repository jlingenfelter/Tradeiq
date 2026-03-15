"""IG Group API integration for fetching portfolio positions."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


IG_LIVE_URL = "https://api.ig.com/gateway/deal"
IG_DEMO_URL = "https://demo-api.ig.com/gateway/deal"


def _get_headers(api_key: str, access_token: str, account_id: str = "") -> dict:
    headers = {
        "X-IG-API-KEY": api_key,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json; charset=UTF-8",
        "Version": "2",
    }
    if account_id:
        headers["IG-ACCOUNT-ID"] = account_id
    return headers


def ig_authenticate(api_key: str, username: str, password: str, environment: str = "live") -> dict:
    """Authenticate with IG REST API and get session tokens."""
    base_url = IG_LIVE_URL if environment == "live" else IG_DEMO_URL

    try:
        resp = httpx.post(
            f"{base_url}/session",
            headers={
                "X-IG-API-KEY": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json; charset=UTF-8",
                "Version": "2",
            },
            json={
                "identifier": username,
                "password": password,
            },
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to IG: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("Invalid IG credentials")
    if resp.status_code != 200:
        raise BadRequestError(f"IG API error: {resp.status_code}")

    data = resp.json()
    # Access token comes from response headers (OAuth tokens) or body
    access_token = resp.headers.get("X-SECURITY-TOKEN", "")
    cst = resp.headers.get("CST", "")

    return {
        "access_token": access_token,
        "cst": cst,
        "account_id": data.get("currentAccountId", ""),
        "accounts": data.get("accounts", []),
    }


def fetch_ig_positions(api_key: str, access_token: str, cst: str, environment: str = "live") -> list[dict]:
    """Fetch all open positions from IG."""
    base_url = IG_LIVE_URL if environment == "live" else IG_DEMO_URL

    headers = {
        "X-IG-API-KEY": api_key,
        "X-SECURITY-TOKEN": access_token,
        "CST": cst,
        "Content-Type": "application/json",
        "Accept": "application/json; charset=UTF-8",
        "Version": "2",
    }

    try:
        resp = httpx.get(
            f"{base_url}/positions",
            headers=headers,
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to IG: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("IG session expired. Please re-authenticate.")
    if resp.status_code != 200:
        raise BadRequestError(f"IG API error: {resp.status_code}")

    data = resp.json()
    return data.get("positions", [])


def import_ig_positions(
    db: Session,
    portfolio: Portfolio,
    api_key: str,
    access_token: str,
    cst: str,
    environment: str = "live",
) -> dict:
    """Import positions from IG into a portfolio."""
    positions_data = fetch_ig_positions(api_key, access_token, cst, environment)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "ig",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="IG Group",
            source_type="ig",
        )
        db.add(account)
        db.flush()

    db.query(Position).filter(Position.account_id == account.id).delete()

    imported = 0
    skipped = 0
    errors = []

    for item in positions_data:
        try:
            pos = item.get("position", {})
            market = item.get("market", {})

            epic = market.get("epic", "")
            instrument_name = market.get("instrumentName", epic)

            size = float(pos.get("size", 0))
            if size == 0:
                skipped += 1
                continue

            level = float(pos.get("level", 0))  # entry price
            currency = pos.get("currency", "GBP")

            position = Position(
                account_id=account.id,
                symbol=epic.replace(".", "-"),
                asset_name=instrument_name,
                asset_type="cfd" if market.get("instrumentType") == "CURRENCIES" else "equity",
                quantity=abs(size),
                cost_basis_per_share=level,
                cost_basis_total=level * abs(size) if level else None,
                currency=currency,
            )
            db.add(position)
            imported += 1
        except (ValueError, KeyError) as e:
            errors.append(f"Position {item.get('market', {}).get('epic', '?')}: {str(e)}")
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
