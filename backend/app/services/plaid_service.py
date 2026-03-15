"""Plaid integration service — Link tokens, token exchange, account sync."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.plaid import PlaidItem, PlaidAccount
from app.models.wealth import WealthContainer, Asset, Liability
from app.models.user import User

import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode


PLAID_ENV_MAP = {
    "sandbox": plaid.Environment.Sandbox,
    "development": plaid.Environment.Development,
    "production": plaid.Environment.Production,
}


def _get_plaid_client() -> plaid_api.PlaidApi:
    """Build a Plaid API client from settings."""
    configuration = plaid.Configuration(
        host=PLAID_ENV_MAP.get(settings.PLAID_ENV, plaid.Environment.Sandbox),
        api_key={
            "clientId": settings.PLAID_CLIENT_ID,
            "secret": settings.PLAID_SECRET,
        },
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def create_link_token(db: Session, user: User) -> str:
    """Create a Plaid Link token for the frontend."""
    client = _get_plaid_client()

    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=str(user.id)),
        client_name="TradeIQ",
        products=[Products("transactions"), Products("auth")],
        country_codes=[CountryCode("US"), CountryCode("GB")],
        language="en",
        redirect_uri=f"{settings.FRONTEND_URL}/plaid/callback",
    )
    response = client.link_token_create(request)
    return response.link_token


def exchange_public_token(db: Session, user: User, public_token: str, metadata: dict) -> dict:
    """Exchange a Plaid public_token for access_token and create PlaidItem."""
    client = _get_plaid_client()

    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)

    access_token = exchange_response.access_token
    item_id = exchange_response.item_id

    # Create or update PlaidItem
    existing = db.query(PlaidItem).filter(PlaidItem.plaid_item_id == item_id).first()
    if existing:
        existing.plaid_access_token = access_token
        existing.status = "active"
        existing.error_code = None
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        plaid_item = existing
    else:
        plaid_item = PlaidItem(
            user_id=user.id,
            plaid_item_id=item_id,
            plaid_access_token=access_token,
            institution_name=metadata.get("institution", {}).get("name"),
            status="active",
        )
        db.add(plaid_item)
        db.commit()
        db.refresh(plaid_item)

    # Immediately sync accounts
    accounts = sync_item_accounts(db, plaid_item)

    return {
        "item_id": str(plaid_item.id),
        "institution_name": plaid_item.institution_name,
        "accounts_synced": len(accounts),
    }


def sync_item_accounts(db: Session, plaid_item: PlaidItem) -> list[dict]:
    """Fetch accounts from Plaid and upsert PlaidAccount records."""
    client = _get_plaid_client()

    request = AccountsGetRequest(access_token=plaid_item.plaid_access_token)
    response = client.accounts_get(request)

    results = []
    for acct in response.accounts:
        existing = db.query(PlaidAccount).filter(
            PlaidAccount.plaid_account_id == acct.account_id
        ).first()

        balances = acct.balances
        if existing:
            existing.name = acct.name
            existing.official_name = acct.official_name
            existing.account_type = acct.type.value if acct.type else "depository"
            existing.account_subtype = acct.subtype.value if acct.subtype else None
            existing.current_balance = balances.current
            existing.available_balance = balances.available
            existing.currency = balances.iso_currency_code or "USD"
            existing.last_synced_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            record = existing
        else:
            record = PlaidAccount(
                plaid_item_id=plaid_item.id,
                plaid_account_id=acct.account_id,
                name=acct.name,
                official_name=acct.official_name,
                account_type=acct.type.value if acct.type else "depository",
                account_subtype=acct.subtype.value if acct.subtype else None,
                current_balance=balances.current,
                available_balance=balances.available,
                currency=balances.iso_currency_code or "USD",
                last_synced_at=datetime.now(timezone.utc),
            )
            db.add(record)
            db.commit()
            db.refresh(record)

        results.append({
            "id": str(record.id),
            "plaid_account_id": record.plaid_account_id,
            "name": record.name,
            "account_type": record.account_type,
            "current_balance": record.current_balance,
            "currency": record.currency,
        })

    # Update item sync status
    plaid_item.status = "active"
    plaid_item.error_code = None
    db.commit()

    return results


def map_plaid_to_wealth(db: Session, user: User, plaid_account: PlaidAccount) -> dict:
    """Map a Plaid account to the wealth tracking system (Asset or Liability)."""
    # Determine or create a WealthContainer
    if not plaid_account.container_id:
        # Find the parent PlaidItem for institution name
        plaid_item = db.query(PlaidItem).filter(PlaidItem.id == plaid_account.plaid_item_id).first()
        institution_name = plaid_item.institution_name if plaid_item else "Linked Account"

        container = WealthContainer(
            user_id=user.id,
            name=f"{institution_name} - {plaid_account.name}",
            container_type="bank" if plaid_account.account_type == "depository" else "brokerage",
            institution_name=institution_name,
            currency=plaid_account.currency,
        )
        db.add(container)
        db.commit()
        db.refresh(container)
        plaid_account.container_id = container.id
        db.commit()
    else:
        container = db.query(WealthContainer).filter(
            WealthContainer.id == plaid_account.container_id
        ).first()

    # Credit and loan accounts become liabilities, others become assets
    if plaid_account.account_type in ("credit", "loan"):
        liability_type = "credit_card" if plaid_account.account_type == "credit" else "loan"
        liability = Liability(
            user_id=user.id,
            container_id=container.id,
            liability_type=liability_type,
            name=plaid_account.name,
            current_balance=abs(plaid_account.current_balance or 0),
            currency=plaid_account.currency,
        )
        db.add(liability)
        db.commit()
        db.refresh(liability)
        return {"type": "liability", "id": str(liability.id), "name": liability.name}
    else:
        asset_class = "cash" if plaid_account.account_type == "depository" else "stock"
        asset = Asset(
            user_id=user.id,
            container_id=container.id,
            asset_class=asset_class,
            name=plaid_account.name,
            current_value=plaid_account.current_balance or 0,
            currency=plaid_account.currency,
            valuation_source="imported",
            liquidity_category="highly_liquid",
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return {"type": "asset", "id": str(asset.id), "name": asset.name}
