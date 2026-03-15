"""Crypto wallet integration — reads on-chain balances for ETH/EVM tokens and BTC."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


def _detect_chain(address: str) -> str:
    """Detect blockchain from address format."""
    if address.startswith("0x") and len(address) == 42:
        return "ethereum"
    if address.startswith(("1", "3", "bc1")):
        return "bitcoin"
    if address.startswith("T") and len(address) == 34:
        return "tron"
    return "ethereum"  # default guess for EVM


def fetch_eth_balances(address: str) -> list[dict]:
    """Fetch ETH and ERC-20 token balances using public APIs."""
    holdings = []

    # Fetch native ETH balance via public RPC
    try:
        resp = httpx.post(
            "https://eth.llamarpc.com",
            json={
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"],
                "id": 1,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            balance_wei = int(data.get("result", "0x0"), 16)
            balance_eth = balance_wei / 1e18
            if balance_eth > 0.0001:
                holdings.append({
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "quantity": balance_eth,
                    "asset_type": "crypto",
                })
    except httpx.RequestError:
        pass

    # Fetch ERC-20 tokens via Ankr API (free, no key required)
    try:
        resp = httpx.post(
            "https://rpc.ankr.com/multichain/?ankr_getAccountBalance",
            json={
                "jsonrpc": "2.0",
                "method": "ankr_getAccountBalance",
                "params": {
                    "walletAddress": address,
                    "blockchain": ["eth"],
                },
                "id": 1,
            },
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            assets = data.get("result", {}).get("assets", [])
            for asset in assets:
                symbol = asset.get("tokenSymbol", "")
                balance = float(asset.get("balanceUsd", 0))
                qty = float(asset.get("balance", 0))
                if balance > 1 and symbol:  # Only include tokens worth > $1
                    holdings.append({
                        "symbol": symbol.upper(),
                        "name": asset.get("tokenName", symbol),
                        "quantity": qty,
                        "asset_type": "crypto",
                    })
    except httpx.RequestError:
        pass

    return holdings


def fetch_btc_balance(address: str) -> list[dict]:
    """Fetch BTC balance using blockchain.info API."""
    try:
        resp = httpx.get(
            f"https://blockchain.info/balance?active={address}",
            timeout=15,
        )
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to query Bitcoin balance: {str(e)}")

    if resp.status_code != 200:
        raise BadRequestError(f"Bitcoin API error: {resp.status_code}")

    data = resp.json()
    addr_data = data.get(address, {})
    balance_sat = addr_data.get("final_balance", 0)
    balance_btc = balance_sat / 1e8

    if balance_btc > 0:
        return [{
            "symbol": "BTC",
            "name": "Bitcoin",
            "quantity": balance_btc,
            "asset_type": "crypto",
        }]
    return []


def validate_wallet_address(address: str) -> dict:
    """Validate a wallet address and detect chain."""
    chain = _detect_chain(address)

    if chain == "ethereum":
        if not address.startswith("0x") or len(address) != 42:
            raise BadRequestError("Invalid Ethereum address format")
    elif chain == "bitcoin":
        if len(address) < 26 or len(address) > 62:
            raise BadRequestError("Invalid Bitcoin address format")

    return {"chain": chain, "address": address, "valid": True}


def fetch_wallet_holdings(address: str) -> tuple[str, list[dict]]:
    """Fetch holdings for any supported wallet address."""
    chain = _detect_chain(address)

    if chain == "ethereum":
        holdings = fetch_eth_balances(address)
    elif chain == "bitcoin":
        holdings = fetch_btc_balance(address)
    else:
        raise BadRequestError(f"Unsupported chain: {chain}")

    return chain, holdings


def import_wallet_positions(
    db: Session,
    portfolio: Portfolio,
    address: str,
) -> dict:
    """Import crypto holdings from a wallet address into a portfolio."""
    chain, holdings = fetch_wallet_holdings(address)

    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id,
        Account.source_type == "crypto_wallet",
        Account.external_account_id == address.lower(),
    ).first()

    if not account:
        chain_label = chain.capitalize()
        short_addr = f"{address[:6]}...{address[-4:]}"
        account = Account(
            portfolio_id=portfolio.id,
            name=f"{chain_label} Wallet ({short_addr})",
            source_type="crypto_wallet",
            external_account_id=address.lower(),
        )
        db.add(account)
        db.flush()

    db.query(Position).filter(Position.account_id == account.id).delete()

    imported = 0
    skipped = 0
    errors = []

    for h in holdings:
        try:
            symbol = h.get("symbol", "")
            qty = h.get("quantity", 0)
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
    return {"imported": imported, "skipped": skipped, "errors": errors[:20], "chain": chain}
