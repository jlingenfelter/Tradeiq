"""Foreign exchange rate service — fetches live FX rates and converts currencies."""

import json
from typing import Optional

import httpx
import redis

from app.config import settings

_redis: Optional[redis.Redis] = None
CACHE_KEY = "fx_rates:{base}"
CACHE_TTL = 3600  # 1 hour


def _get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            return None
    return _redis


def get_fx_rates(base: str = "USD") -> dict[str, float]:
    """Get FX rates with base currency. Cached in Redis for 1 hour."""
    r = _get_redis()
    cache_key = CACHE_KEY.format(base=base.upper())

    # Try cache first
    if r:
        try:
            cached = r.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    # Fetch from frankfurter.dev (free, no API key)
    rates = _fetch_rates_frankfurter(base)

    # Fallback to exchangerate-api if frankfurter fails
    if not rates:
        rates = _fetch_rates_exchangerate(base)

    if not rates:
        # Return identity if both fail
        return {base.upper(): 1.0}

    # Always include the base currency itself
    rates[base.upper()] = 1.0

    # Cache
    if r:
        try:
            r.set(cache_key, json.dumps(rates), ex=CACHE_TTL)
        except Exception:
            pass

    return rates


def _fetch_rates_frankfurter(base: str) -> dict[str, float] | None:
    try:
        resp = httpx.get(
            f"https://api.frankfurter.dev/v1/latest?base={base.upper()}",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("rates", {})
    except (httpx.RequestError, httpx.TimeoutException):
        pass
    return None


def _fetch_rates_exchangerate(base: str) -> dict[str, float] | None:
    try:
        resp = httpx.get(
            f"https://open.er-api.com/v6/latest/{base.upper()}",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("result") == "success":
                return data.get("rates", {})
    except (httpx.RequestError, httpx.TimeoutException):
        pass
    return None


def convert(amount: float, from_currency: str, to_currency: str, rates: dict[str, float] | None = None) -> float:
    """Convert an amount between currencies."""
    from_cur = from_currency.upper()
    to_cur = to_currency.upper()

    if from_cur == to_cur:
        return amount

    if rates is None:
        rates = get_fx_rates(from_cur)

    # If rates are based on from_currency
    if from_cur in rates and rates[from_cur] == 1.0:
        rate = rates.get(to_cur)
        if rate:
            return amount * rate

    # If rates are based on a different currency, do cross-rate
    from_rate = rates.get(from_cur, 1.0)
    to_rate = rates.get(to_cur)
    if to_rate and from_rate:
        return amount * (to_rate / from_rate)

    return amount  # Can't convert, return original
