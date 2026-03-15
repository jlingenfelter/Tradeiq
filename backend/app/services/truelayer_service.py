"""TrueLayer integration service — OAuth flow, account sync for UK/EU banks."""

import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.plaid import PlaidItem, PlaidAccount
from app.models.wealth import WealthContainer, Asset, Liability
from app.models.user import User


TRUELAYER_AUTH_URLS = {
    "sandbox": "https://auth.truelayer-sandbox.com",
    "live": "https://auth.truelayer.com",
}

TRUELAYER_API_URLS = {
    "sandbox": "https://api.truelayer-sandbox.com",
    "live": "https://api.truelayer.com",
}


def _auth_base() -> str:
    return TRUELAYER_AUTH_URLS.get(settings.TRUELAYER_ENV, TRUELAYER_AUTH_URLS["sandbox"])


def _api_base() -> str:
    return TRUELAYER_API_URLS.get(settings.TRUELAYER_ENV, TRUELAYER_API_URLS["sandbox"])


def create_auth_url(db: Session, user: User) -> str:
    """Generate the TrueLayer OAuth authorization URL."""
    params = {
        "response_type": "code",
        "client_id": settings.TRUELAYER_CLIENT_ID,
        "redirect_uri": f"{settings.FRONTEND_URL}/truelayer/callback",
        "scope": "info accounts balance cards",
        "state": str(user.id),
        "providers": "uk-ob-all uk-oauth-all",
    }
    return f"{_auth_base()}/?{urlencode(params)}"


async def exchange_code(db: Session, user: User, code: str) -> dict:
    """Exchange the TrueLayer authorization code for tokens and store as a PlaidItem."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_auth_base()}/connect/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.TRUELAYER_CLIENT_ID,
                "client_secret": settings.TRUELAYER_CLIENT_SECRET,
                "redirect_uri": f"{settings.FRONTEND_URL}/truelayer/callback",
                "code": code,
            },
        )
        response.raise_for_status()
        token_data = response.json()

    access_token = token_data["access_token"]
    # Store as a PlaidItem record (reuse model for both providers)
    truelayer_item_id = f"truelayer_{user.id}_{uuid.uuid4().hex[:8]}"

    plaid_item = PlaidItem(
        user_id=user.id,
        plaid_item_id=truelayer_item_id,
        plaid_access_token=access_token,
        institution_name="TrueLayer",
        status="active",
    )
    db.add(plaid_item)
    db.commit()
    db.refresh(plaid_item)

    return {
        "item_id": str(plaid_item.id),
        "access_token_preview": access_token[:8] + "...",
    }


async def sync_accounts(db: Session, user: User, access_token: str) -> list[dict]:
    """Fetch accounts from TrueLayer and upsert PlaidAccount records."""
    results = []

    # Find the PlaidItem for this token
    plaid_item = db.query(PlaidItem).filter(
        PlaidItem.user_id == user.id,
        PlaidItem.plaid_access_token == access_token,
    ).first()
    if not plaid_item:
        return []

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        # Fetch bank accounts
        accounts_resp = await client.get(f"{_api_base()}/data/v1/accounts", headers=headers)
        if accounts_resp.status_code == 200:
            accounts_data = accounts_resp.json().get("results", [])
            for acct in accounts_data:
                account_id = acct["account_id"]

                # Fetch balance for each account
                balance_resp = await client.get(
                    f"{_api_base()}/data/v1/accounts/{account_id}/balance",
                    headers=headers,
                )
                balance = 0.0
                currency = "GBP"
                if balance_resp.status_code == 200:
                    balance_data = balance_resp.json().get("results", [])
                    if balance_data:
                        balance = balance_data[0].get("current", 0.0)
                        currency = balance_data[0].get("currency", "GBP")

                existing = db.query(PlaidAccount).filter(
                    PlaidAccount.plaid_account_id == account_id
                ).first()

                if existing:
                    existing.name = acct.get("display_name", acct.get("account_id"))
                    existing.current_balance = balance
                    existing.currency = currency
                    existing.last_synced_at = datetime.now(timezone.utc)
                    db.commit()
                    record = existing
                else:
                    record = PlaidAccount(
                        plaid_item_id=plaid_item.id,
                        plaid_account_id=account_id,
                        name=acct.get("display_name", account_id),
                        official_name=acct.get("provider", {}).get("display_name"),
                        account_type="depository",
                        account_subtype=acct.get("account_type", "TRANSACTION"),
                        current_balance=balance,
                        currency=currency,
                        last_synced_at=datetime.now(timezone.utc),
                    )
                    db.add(record)
                    db.commit()
                    db.refresh(record)

                results.append({
                    "id": str(record.id),
                    "name": record.name,
                    "account_type": record.account_type,
                    "current_balance": record.current_balance,
                    "currency": record.currency,
                })

        # Fetch credit cards
        cards_resp = await client.get(f"{_api_base()}/data/v1/cards", headers=headers)
        if cards_resp.status_code == 200:
            cards_data = cards_resp.json().get("results", [])
            for card in cards_data:
                card_id = card["account_id"]

                balance_resp = await client.get(
                    f"{_api_base()}/data/v1/cards/{card_id}/balance",
                    headers=headers,
                )
                balance = 0.0
                currency = "GBP"
                if balance_resp.status_code == 200:
                    balance_data = balance_resp.json().get("results", [])
                    if balance_data:
                        balance = balance_data[0].get("current", 0.0)
                        currency = balance_data[0].get("currency", "GBP")

                existing = db.query(PlaidAccount).filter(
                    PlaidAccount.plaid_account_id == card_id
                ).first()

                if existing:
                    existing.name = card.get("display_name", card_id)
                    existing.current_balance = balance
                    existing.currency = currency
                    existing.last_synced_at = datetime.now(timezone.utc)
                    db.commit()
                    record = existing
                else:
                    record = PlaidAccount(
                        plaid_item_id=plaid_item.id,
                        plaid_account_id=card_id,
                        name=card.get("display_name", card_id),
                        official_name=card.get("provider", {}).get("display_name"),
                        account_type="credit",
                        account_subtype="credit_card",
                        current_balance=balance,
                        currency=currency,
                        last_synced_at=datetime.now(timezone.utc),
                    )
                    db.add(record)
                    db.commit()
                    db.refresh(record)

                results.append({
                    "id": str(record.id),
                    "name": record.name,
                    "account_type": record.account_type,
                    "current_balance": record.current_balance,
                    "currency": record.currency,
                })

    return results
