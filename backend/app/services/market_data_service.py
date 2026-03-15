import json
from datetime import datetime, timezone

import redis
from sqlalchemy.orm import Session

from app.config import settings
from app.models.market_data import AssetMetadata, PriceSnapshot
from app.providers.market_data_provider import (
    MarketDataProvider, YFinanceProvider, Quote, AssetInfo,
)

PRICE_CACHE_TTL = 300  # 5 minutes
METADATA_CACHE_TTL = 86400  # 24 hours

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def get_provider() -> MarketDataProvider:
    return YFinanceProvider()


def get_cached_quote(symbol: str) -> Quote | None:
    r = get_redis()
    cached = r.get(f"quote:{symbol.upper()}")
    if cached:
        data = json.loads(cached)
        return Quote(
            symbol=data["symbol"],
            price=data["price"],
            previous_close=data.get("previous_close"),
            currency=data["currency"],
            as_of=datetime.fromisoformat(data["as_of"]),
        )
    return None


def cache_quote(quote: Quote) -> None:
    r = get_redis()
    r.setex(
        f"quote:{quote.symbol}",
        PRICE_CACHE_TTL,
        json.dumps({
            "symbol": quote.symbol,
            "price": quote.price,
            "previous_close": quote.previous_close,
            "currency": quote.currency,
            "as_of": quote.as_of.isoformat(),
        }),
    )


def fetch_quote(symbol: str) -> Quote | None:
    cached = get_cached_quote(symbol)
    if cached:
        return cached
    provider = get_provider()
    quote = provider.get_quote(symbol)
    if quote:
        cache_quote(quote)
    return quote


def fetch_quotes(symbols: list[str]) -> dict[str, Quote]:
    results: dict[str, Quote] = {}
    uncached: list[str] = []

    for symbol in symbols:
        cached = get_cached_quote(symbol)
        if cached:
            results[symbol.upper()] = cached
        else:
            uncached.append(symbol)

    if uncached:
        provider = get_provider()
        fresh = provider.get_quotes(uncached)
        for sym, quote in fresh.items():
            cache_quote(quote)
            results[sym] = quote

    return results


def fetch_and_store_metadata(db: Session, symbol: str) -> AssetMetadata | None:
    provider = get_provider()
    info = provider.get_asset_metadata(symbol)
    if not info:
        return None

    metadata = db.query(AssetMetadata).filter(AssetMetadata.symbol == symbol.upper()).first()
    if metadata:
        metadata.asset_name = info.name
        metadata.sector = info.sector
        metadata.industry = info.industry
        metadata.country = info.country
        metadata.exchange = info.exchange
        metadata.asset_type = info.asset_type
        metadata.market_cap_bucket = info.market_cap_bucket
    else:
        metadata = AssetMetadata(
            symbol=symbol.upper(),
            asset_name=info.name,
            sector=info.sector,
            industry=info.industry,
            country=info.country,
            exchange=info.exchange,
            asset_type=info.asset_type,
            market_cap_bucket=info.market_cap_bucket,
        )
        db.add(metadata)

    db.commit()
    db.refresh(metadata)
    return metadata


def store_price_snapshot(db: Session, quote: Quote) -> PriceSnapshot:
    snapshot = PriceSnapshot(
        symbol=quote.symbol,
        price=quote.price,
        previous_close=quote.previous_close,
        currency=quote.currency,
        as_of=quote.as_of,
        source="yfinance",
    )
    db.add(snapshot)
    db.commit()
    return snapshot


def refresh_market_data_for_symbols(db: Session, symbols: list[str]) -> dict[str, Quote]:
    quotes = fetch_quotes(symbols)
    for symbol in symbols:
        # Ensure metadata exists
        existing = db.query(AssetMetadata).filter(AssetMetadata.symbol == symbol.upper()).first()
        if not existing:
            fetch_and_store_metadata(db, symbol)
    return quotes


def get_benchmark_info(symbol: str = "SPY") -> dict:
    r = get_redis()
    cached = r.get(f"benchmark:{symbol}")
    if cached:
        return json.loads(cached)

    provider = get_provider()
    data = provider.get_benchmark_data(symbol)
    r.setex(f"benchmark:{symbol}", METADATA_CACHE_TTL, json.dumps(data))
    return data
