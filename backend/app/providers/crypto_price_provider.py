"""Crypto price provider using CoinGecko free API (no key required)."""

import httpx
from datetime import datetime, timezone
from dataclasses import dataclass

from app.providers.market_data_provider import Quote, AssetInfo


# Map common crypto ticker symbols to CoinGecko IDs
SYMBOL_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "SOL": "solana",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "POL": "matic-network",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "AAVE": "aave",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "FIL": "filecoin",
    "NEAR": "near",
    "ARB": "arbitrum",
    "OP": "optimism",
    "APT": "aptos",
    "SUI": "sui",
    "SEI": "sei-network",
    "INJ": "injective-protocol",
    "TIA": "celestia",
    "RENDER": "render-token",
    "RNDR": "render-token",
    "FET": "fetch-ai",
    "GRT": "the-graph",
    "IMX": "immutable-x",
    "MKR": "maker",
    "SNX": "havven",
    "CRV": "curve-dao-token",
    "LDO": "lido-dao",
    "RPL": "rocket-pool",
    "COMP": "compound-governance-token",
    "SUSHI": "sushi",
    "BAL": "balancer",
    "1INCH": "1inch",
    "ENS": "ethereum-name-service",
    "PEPE": "pepe",
    "SHIB": "shiba-inu",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
    "FLOKI": "floki",
    "DAI": "dai",
    "WBTC": "wrapped-bitcoin",
    "WETH": "weth",
    "STETH": "staked-ether",
    "WSTETH": "wrapped-steth",
    "RETH": "rocket-pool-eth",
    "CBETH": "coinbase-wrapped-staked-eth",
    "EIGEN": "eigenlayer",
    "ENA": "ethena",
    "ETHFI": "ether-fi",
    "PENDLE": "pendle",
    "BLUR": "blur",
    "SAFE": "safe",
    "SKY": "sky-mavis",
    "MORPHO": "morpho",
    "XLM": "stellar",
    "ALGO": "algorand",
    "VET": "vechain",
    "HBAR": "hedera-hashgraph",
    "ICP": "internet-computer",
    "FTM": "fantom",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "AXS": "axie-infinity",
    "THETA": "theta-token",
    "EOS": "eos",
    "XTZ": "tezos",
    "KAVA": "kava",
    "ROSE": "oasis-network",
    "ZEC": "zcash",
    "XMR": "monero",
    "BCH": "bitcoin-cash",
    "ETC": "ethereum-classic",
    "TRX": "tron",
    "TON": "the-open-network",
    "TUSD": "true-usd",
    "BUSD": "binance-usd",
    "GUSD": "gemini-dollar",
    "USDD": "usdd",
    "PYUSD": "paypal-usd",
}

# Names for crypto assets
CRYPTO_NAMES = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "USDT": "Tether",
    "USDC": "USD Coin",
    "BNB": "BNB",
    "XRP": "XRP",
    "ADA": "Cardano",
    "DOGE": "Dogecoin",
    "SOL": "Solana",
    "DOT": "Polkadot",
    "MATIC": "Polygon",
    "POL": "Polygon",
    "AVAX": "Avalanche",
    "LINK": "Chainlink",
    "UNI": "Uniswap",
    "AAVE": "Aave",
    "ATOM": "Cosmos",
    "LTC": "Litecoin",
    "DAI": "Dai",
    "WBTC": "Wrapped Bitcoin",
    "STETH": "Lido Staked ETH",
    "ARB": "Arbitrum",
    "OP": "Optimism",
    "RENDER": "Render",
    "RNDR": "Render",
    "FET": "Fetch.ai",
    "PEPE": "Pepe",
    "SHIB": "Shiba Inu",
    "TON": "Toncoin",
    "TRX": "TRON",
    "BCH": "Bitcoin Cash",
    "XMR": "Monero",
}

COINGECKO_API = "https://api.coingecko.com/api/v3"


def is_crypto_symbol(symbol: str) -> bool:
    """Check if a symbol is a known cryptocurrency."""
    return symbol.upper() in SYMBOL_TO_COINGECKO_ID


def get_crypto_quotes(symbols: list[str]) -> dict[str, Quote]:
    """Fetch current prices for multiple crypto symbols from CoinGecko."""
    results = {}
    if not symbols:
        return results

    # Map symbols to CoinGecko IDs
    id_to_symbol = {}
    for sym in symbols:
        cg_id = SYMBOL_TO_COINGECKO_ID.get(sym.upper())
        if cg_id:
            id_to_symbol[cg_id] = sym.upper()

    if not id_to_symbol:
        return results

    ids_param = ",".join(id_to_symbol.keys())
    try:
        resp = httpx.get(
            f"{COINGECKO_API}/simple/price",
            params={
                "ids": ids_param,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for cg_id, sym in id_to_symbol.items():
            price_data = data.get(cg_id, {})
            price = price_data.get("usd")
            if price is not None:
                change_24h = price_data.get("usd_24h_change")
                prev_close = price / (1 + change_24h / 100) if change_24h else None
                results[sym] = Quote(
                    symbol=sym,
                    price=float(price),
                    previous_close=float(prev_close) if prev_close else None,
                    currency="USD",
                    as_of=datetime.now(timezone.utc),
                )
    except Exception:
        # Fallback: try one by one
        for cg_id, sym in id_to_symbol.items():
            try:
                quote = get_single_crypto_quote(sym)
                if quote:
                    results[sym] = quote
            except Exception:
                continue

    return results


def get_single_crypto_quote(symbol: str) -> Quote | None:
    """Fetch a single crypto price from CoinGecko."""
    cg_id = SYMBOL_TO_COINGECKO_ID.get(symbol.upper())
    if not cg_id:
        return None

    try:
        resp = httpx.get(
            f"{COINGECKO_API}/simple/price",
            params={
                "ids": cg_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get(cg_id, {})
        price = data.get("usd")
        if price is None:
            return None

        change_24h = data.get("usd_24h_change")
        prev_close = price / (1 + change_24h / 100) if change_24h else None

        return Quote(
            symbol=symbol.upper(),
            price=float(price),
            previous_close=float(prev_close) if prev_close else None,
            currency="USD",
            as_of=datetime.now(timezone.utc),
        )
    except Exception:
        return None


def get_crypto_metadata(symbol: str) -> AssetInfo | None:
    """Get metadata for a crypto asset."""
    sym = symbol.upper()
    cg_id = SYMBOL_TO_COINGECKO_ID.get(sym)
    if not cg_id:
        return None

    name = CRYPTO_NAMES.get(sym, sym)

    # Try to get market cap from CoinGecko for bucket classification
    bucket = None
    try:
        resp = httpx.get(
            f"{COINGECKO_API}/simple/price",
            params={"ids": cg_id, "vs_currencies": "usd", "include_market_cap": "true"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get(cg_id, {})
        market_cap = data.get("usd_market_cap")
        if market_cap:
            if market_cap >= 200_000_000_000:
                bucket = "mega"
            elif market_cap >= 10_000_000_000:
                bucket = "large"
            elif market_cap >= 2_000_000_000:
                bucket = "mid"
            elif market_cap >= 300_000_000:
                bucket = "small"
            else:
                bucket = "micro"
    except Exception:
        pass

    return AssetInfo(
        symbol=sym,
        name=name,
        sector="Crypto",
        industry="Cryptocurrency",
        country=None,
        exchange="Decentralized",
        asset_type="crypto",
        market_cap_bucket=bucket,
    )
