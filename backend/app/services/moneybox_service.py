"""Moneybox integration — login with email/password, fetch ISA/GIA/LISA portfolio data."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


MONEYBOX_BASE_URL = "https://api.moneyboxapp.com"
MONEYBOX_HEADERS = {
    "AppId": "8cb2237d0679ca88db6464",
    "appVersion": "8.41.0",
    "apiVersion": "9",
    "Content-Type": "application/json",
}


def _login(email: str, password: str) -> str:
    """Authenticate with Moneybox and return a bearer token."""
    try:
        resp = httpx.post(
            f"{MONEYBOX_BASE_URL}/users/login",
            headers=MONEYBOX_HEADERS,
            json={"Email": email, "Password": password},
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to connect to Moneybox: {str(e)}")

    if resp.status_code == 401:
        raise BadRequestError("Invalid Moneybox email or password")
    if resp.status_code == 400:
        data = resp.json()
        msg = data.get("Message") or data.get("message") or "Bad request"
        raise BadRequestError(f"Moneybox login failed: {msg}")
    if resp.status_code != 200:
        raise BadRequestError(f"Moneybox API error: {resp.status_code}")

    data = resp.json()
    token = data.get("Session", {}).get("BearerToken")
    if not token:
        raise BadRequestError("No bearer token in Moneybox login response")
    return token


def _auth_headers(bearer_token: str) -> dict:
    return {**MONEYBOX_HEADERS, "Authorization": f"Bearer {bearer_token}"}


def fetch_moneybox_products(email: str, password: str) -> list[dict]:
    """Login and fetch all investor products (accounts + holdings)."""
    token = _login(email, password)

    try:
        resp = httpx.get(
            f"{MONEYBOX_BASE_URL}/investorproducts",
            headers=_auth_headers(token),
            timeout=30,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to fetch Moneybox products: {str(e)}")

    if resp.status_code != 200:
        raise BadRequestError(f"Moneybox products API error: {resp.status_code}")

    data = resp.json()
    products = data.get("InvestorProducts") or data.get("Products") or []
    if isinstance(data, list):
        products = data

    holdings = []
    for product in products:
        product_name = product.get("Name") or product.get("ProductName") or "Moneybox Account"
        product_type = product.get("Type") or product.get("ProductType") or ""

        # Map Moneybox product types to asset types
        if "isa" in product_type.lower() or "ISA" in product_name:
            asset_type = "etf"
        elif "pension" in product_type.lower() or "SIPP" in product_name.upper():
            asset_type = "pension"
        else:
            asset_type = "mutual_fund"

        # Total value for the product
        total_value = (
            product.get("TotalValue")
            or product.get("InvestedAmount")
            or product.get("Moneybox", 0)
        )

        # Try to get individual fund breakdowns
        investments = product.get("Investments") or product.get("Funds") or []
        if investments:
            for inv in investments:
                fund_name = inv.get("FundName") or inv.get("Name") or product_name
                value = inv.get("Value") or inv.get("CurrentValue") or 0
                cost = inv.get("InvestedAmount") or inv.get("ContributionsNet") or 0

                if value > 0:
                    holdings.append({
                        "symbol": f"MB-{product_type.upper()}" if product_type else "MB-FUND",
                        "name": f"{product_name} — {fund_name}",
                        "quantity": 1,
                        "market_value": float(value),
                        "cost_basis": float(cost) if cost else None,
                        "asset_type": asset_type,
                        "currency": "GBP",
                    })
        elif total_value and float(total_value) > 0:
            contributions = product.get("TotalContributions") or product.get("ContributionsNet") or 0
            holdings.append({
                "symbol": f"MB-{product_type.upper()}" if product_type else "MB-FUND",
                "name": product_name,
                "quantity": 1,
                "market_value": float(total_value),
                "cost_basis": float(contributions) if contributions else None,
                "asset_type": asset_type,
                "currency": "GBP",
            })

    return holdings


def test_moneybox_connection(email: str, password: str) -> dict:
    """Test Moneybox credentials and return account summary."""
    holdings = fetch_moneybox_products(email, password)
    total_value = sum(h["market_value"] for h in holdings)
    return {
        "success": True,
        "account_count": len(holdings),
        "total_value": round(total_value, 2),
        "currency": "GBP",
        "message": f"Found {len(holdings)} Moneybox product(s) worth £{total_value:,.2f}",
    }


def import_moneybox_positions(
    db: Session,
    portfolio: Portfolio,
    email: str,
    password: str,
) -> dict:
    """Import Moneybox holdings into a portfolio."""
    holdings = fetch_moneybox_products(email, password)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "moneybox",
    ).first()

    if not account:
        account = Account(
            portfolio_id=portfolio.id,
            name="Moneybox",
            source_type="moneybox",
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
            position = Position(
                account_id=account.id,
                symbol=h["symbol"],
                asset_name=h["name"],
                asset_type=h["asset_type"],
                quantity=h["quantity"],
                cost_basis_total=h.get("cost_basis"),
                currency=h["currency"],
            )
            # Store market value directly since these are fund products
            if h["market_value"]:
                position.cost_basis_per_share = h["market_value"]
            db.add(position)
            imported += 1
        except (ValueError, KeyError) as e:
            errors.append(f"{h.get('name', '?')}: {str(e)}")
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
