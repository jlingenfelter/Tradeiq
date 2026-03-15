from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.market_data_service import refresh_market_data_for_symbols, fetch_and_store_metadata


@celery_app.task(name="refresh_prices")
def refresh_prices(symbols: list[str]) -> dict:
    db = SessionLocal()
    try:
        quotes = refresh_market_data_for_symbols(db, symbols)
        return {sym: q.price for sym, q in quotes.items()}
    finally:
        db.close()


@celery_app.task(name="refresh_metadata")
def refresh_metadata(symbol: str) -> dict | None:
    db = SessionLocal()
    try:
        metadata = fetch_and_store_metadata(db, symbol)
        if metadata:
            return {"symbol": metadata.symbol, "sector": metadata.sector, "country": metadata.country}
        return None
    finally:
        db.close()
