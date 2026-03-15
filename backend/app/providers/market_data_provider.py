from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Quote:
    symbol: str
    price: float
    previous_close: float | None
    currency: str
    as_of: datetime


@dataclass
class AssetInfo:
    symbol: str
    name: str
    sector: str | None
    industry: str | None
    country: str | None
    exchange: str | None
    asset_type: str
    market_cap_bucket: str | None


@dataclass
class HistoricalPrice:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketDataProvider(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote | None:
        ...

    @abstractmethod
    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        ...

    @abstractmethod
    def get_asset_metadata(self, symbol: str) -> AssetInfo | None:
        ...

    @abstractmethod
    def get_historical_prices(self, symbol: str, period: str = "1y") -> list[HistoricalPrice]:
        ...

    @abstractmethod
    def get_benchmark_data(self, symbol: str = "SPY") -> dict:
        ...


class YFinanceProvider(MarketDataProvider):
    def get_quote(self, symbol: str) -> Quote | None:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            price = info.get("lastPrice") or info.get("last_price")
            if price is None:
                return None
            return Quote(
                symbol=symbol.upper(),
                price=float(price),
                previous_close=float(info.get("previousClose") or info.get("previous_close") or 0),
                currency=str(info.get("currency", "USD")),
                as_of=datetime.utcnow(),
            )
        except Exception:
            return None

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        import yfinance as yf
        results = {}
        if not symbols:
            return results
        try:
            tickers = yf.Tickers(" ".join(symbols))
            for symbol in symbols:
                try:
                    ticker = tickers.tickers.get(symbol.upper())
                    if ticker is None:
                        continue
                    info = ticker.fast_info
                    price = info.get("lastPrice") or info.get("last_price")
                    if price is None:
                        continue
                    results[symbol.upper()] = Quote(
                        symbol=symbol.upper(),
                        price=float(price),
                        previous_close=float(info.get("previousClose") or info.get("previous_close") or 0),
                        currency=str(info.get("currency", "USD")),
                        as_of=datetime.utcnow(),
                    )
                except Exception:
                    continue
        except Exception:
            # Fallback: fetch one by one
            for symbol in symbols:
                quote = self.get_quote(symbol)
                if quote:
                    results[symbol.upper()] = quote
        return results

    def get_asset_metadata(self, symbol: str) -> AssetInfo | None:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info or "shortName" not in info:
                return None

            market_cap = info.get("marketCap")
            bucket = None
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

            return AssetInfo(
                symbol=symbol.upper(),
                name=info.get("shortName", symbol),
                sector=info.get("sector"),
                industry=info.get("industry"),
                country=info.get("country"),
                exchange=info.get("exchange"),
                asset_type="etf" if info.get("quoteType") == "ETF" else "equity",
                market_cap_bucket=bucket,
            )
        except Exception:
            return None

    def get_historical_prices(self, symbol: str, period: str = "1y") -> list[HistoricalPrice]:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            results = []
            for date, row in hist.iterrows():
                results.append(HistoricalPrice(
                    date=date.to_pydatetime(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                ))
            return results
        except Exception:
            return []

    def get_benchmark_data(self, symbol: str = "SPY") -> dict:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            # Get sector weights for ETFs like SPY
            sector_weights = {}
            if hasattr(ticker, "fund_sector_weightings"):
                try:
                    for sector, weight in ticker.fund_sector_weightings.items():
                        sector_weights[sector] = float(weight) * 100
                except Exception:
                    pass

            # Default S&P 500 approximate sector weights
            if not sector_weights:
                sector_weights = {
                    "Technology": 31.0,
                    "Healthcare": 12.5,
                    "Financial Services": 13.0,
                    "Consumer Cyclical": 10.5,
                    "Communication Services": 9.0,
                    "Industrials": 8.5,
                    "Consumer Defensive": 6.0,
                    "Energy": 3.5,
                    "Utilities": 2.5,
                    "Real Estate": 2.0,
                    "Basic Materials": 1.5,
                }

            return {
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "sector_weights": sector_weights,
            }
        except Exception:
            return {
                "symbol": symbol,
                "name": "S&P 500",
                "sector_weights": {
                    "Technology": 31.0,
                    "Healthcare": 12.5,
                    "Financial Services": 13.0,
                    "Consumer Cyclical": 10.5,
                    "Communication Services": 9.0,
                    "Industrials": 8.5,
                    "Consumer Defensive": 6.0,
                    "Energy": 3.5,
                    "Utilities": 2.5,
                    "Real Estate": 2.0,
                    "Basic Materials": 1.5,
                },
            }
