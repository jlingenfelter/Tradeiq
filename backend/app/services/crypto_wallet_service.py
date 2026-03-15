"""Crypto wallet integration — reads on-chain balances for ETH/EVM tokens and BTC."""

import httpx
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.core.exceptions import BadRequestError


# Multiple RPC endpoints for fallback
ETH_RPC_ENDPOINTS = [
    "https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth",
    "https://ethereum.publicnode.com",
    "https://1rpc.io/eth",
    "https://eth.drpc.org",
]


def _detect_chain(address: str) -> str:
    """Detect blockchain from address format."""
    if address.startswith("0x") and len(address) == 42:
        return "ethereum"
    if address.startswith(("1", "3", "bc1")):
        return "bitcoin"
    return "ethereum"


def _eth_rpc_call(method: str, params: list, timeout: int = 10) -> dict | None:
    """Try multiple RPC endpoints until one works."""
    for endpoint in ETH_RPC_ENDPOINTS:
        try:
            resp = httpx.post(
                endpoint,
                json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data:
                    return data
        except (httpx.RequestError, httpx.TimeoutException):
            continue
    return None


def fetch_eth_balances(address: str) -> list[dict]:
    """Fetch ETH and ERC-20 token balances using multiple fallback APIs."""
    holdings = []
    errors_log = []

    # 1. Fetch native ETH balance via RPC (with fallback endpoints)
    data = _eth_rpc_call("eth_getBalance", [address, "latest"])
    if data:
        try:
            balance_wei = int(data["result"], 16)
            balance_eth = balance_wei / 1e18
            if balance_eth > 0:
                holdings.append({
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "quantity": round(balance_eth, 8),
                    "asset_type": "crypto",
                })
        except (ValueError, KeyError) as e:
            errors_log.append(f"ETH balance parse error: {e}")
    else:
        errors_log.append("Could not fetch ETH balance from any RPC endpoint")

    # 2. Fetch ERC-20 tokens via Blockscout API (free, no key needed)
    blockscout_ok = False
    try:
        resp = httpx.get(
            f"https://eth.blockscout.com/api/v2/addresses/{address}/token-balances",
            timeout=20,
        )
        if resp.status_code == 200:
            tokens = resp.json()
            # Known legitimate tokens — filter out spam
            known_symbols = {
                "USDT", "USDC", "DAI", "WBTC", "WETH", "LINK", "UNI", "AAVE",
                "MATIC", "SHIB", "ARB", "OP", "LDO", "MKR", "SNX", "COMP",
                "CRV", "BAL", "SUSHI", "YFI", "1INCH", "ENS", "RPL", "GRT",
                "FET", "RNDR", "IMX", "PEPE", "APE", "DYDX", "BLUR", "PENDLE",
                "EIGEN", "ENA", "ETHFI", "SAFE", "MORPHO", "SKY",
                "stETH", "rETH", "cbETH", "wstETH", "LUSD", "FRAX", "USDD",
                "GHO", "crvUSD", "PYUSD", "TUSD", "BUSD", "GUSD", "RAI",
            }
            for t in tokens:
                token_info = t.get("token", {})
                symbol = token_info.get("symbol", "")
                name = token_info.get("name", symbol)
                decimals = int(token_info.get("decimals") or 18)
                raw_value = t.get("value", "0")

                if not symbol or not raw_value:
                    continue

                # Only include known tokens to filter out airdrop spam
                if symbol not in known_symbols:
                    continue

                try:
                    qty = int(raw_value) / (10 ** decimals)
                except (ValueError, OverflowError):
                    continue

                if qty <= 0.001:
                    continue

                # Skip if we already have ETH
                if symbol.upper() in ("ETH", "WETH") and any(h["symbol"] == "ETH" for h in holdings):
                    continue

                holdings.append({
                    "symbol": symbol.upper(),
                    "name": name,
                    "quantity": round(qty, 8),
                    "asset_type": "crypto",
                })
            blockscout_ok = True
    except (httpx.RequestError, httpx.TimeoutException):
        errors_log.append("Blockscout API unavailable for token balances")

    # 3. Fallback: check common ERC-20 tokens via direct RPC balanceOf calls
    if not blockscout_ok and len(holdings) <= 1:
        common_tokens = {
            "0xdAC17F958D2ee523a2206206994597C13D831ec7": ("USDT", "Tether USD", 6),
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": ("USDC", "USD Coin", 6),
            "0x6B175474E89094C44Da98b954EedeAC495271d0F": ("DAI", "Dai Stablecoin", 18),
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": ("WBTC", "Wrapped BTC", 8),
            "0x514910771AF9Ca656af840dff83E8264EcF986CA": ("LINK", "Chainlink", 18),
            "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": ("UNI", "Uniswap", 18),
            "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9": ("AAVE", "Aave", 18),
            "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84": ("stETH", "Lido Staked Ether", 18),
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": ("WETH", "Wrapped Ether", 18),
        }
        balanceof_sig = "0x70a08231" + address[2:].lower().zfill(64)

        for contract, (symbol, name, decimals) in common_tokens.items():
            data = _eth_rpc_call("eth_call", [{"to": contract, "data": balanceof_sig}, "latest"])
            if data and data.get("result") and data["result"] != "0x":
                try:
                    raw = int(data["result"], 16)
                    if raw > 0:
                        qty = raw / (10 ** decimals)
                        if qty > 0.001:
                            holdings.append({
                                "symbol": symbol,
                                "name": name,
                                "quantity": round(qty, 8),
                                "asset_type": "crypto",
                            })
                except (ValueError, OverflowError):
                    pass

    return holdings


def fetch_btc_balance(address: str) -> list[dict]:
    """Fetch BTC balance using multiple API providers."""
    # Try blockchain.info first
    providers = [
        f"https://blockchain.info/balance?active={address}",
        f"https://blockstream.info/api/address/{address}",
    ]

    # Provider 1: blockchain.info
    try:
        resp = httpx.get(providers[0], timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            addr_data = data.get(address, {})
            balance_sat = addr_data.get("final_balance", 0)
            balance_btc = balance_sat / 1e8
            if balance_btc > 0:
                return [{
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "quantity": round(balance_btc, 8),
                    "asset_type": "crypto",
                }]
            return []
    except (httpx.RequestError, httpx.TimeoutException):
        pass

    # Provider 2: blockstream.info
    try:
        resp = httpx.get(providers[1], timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            funded = data.get("chain_stats", {}).get("funded_txo_sum", 0)
            spent = data.get("chain_stats", {}).get("spent_txo_sum", 0)
            balance_sat = funded - spent
            balance_btc = balance_sat / 1e8
            if balance_btc > 0:
                return [{
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "quantity": round(balance_btc, 8),
                    "asset_type": "crypto",
                }]
            return []
    except (httpx.RequestError, httpx.TimeoutException):
        pass

    raise BadRequestError("Could not reach any Bitcoin API. Please try again.")


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

    if not holdings:
        return {
            "imported": 0,
            "skipped": 0,
            "errors": [f"No tokens found in this {chain} wallet. The wallet may be empty or the APIs could not be reached."],
            "chain": chain,
        }

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
