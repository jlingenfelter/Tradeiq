"""Resolve ticker symbols to full company/asset names using yfinance metadata."""

from sqlalchemy.orm import Session

from app.models.market_data import AssetMetadata


def resolve_stock_names(db: Session, symbols: list[str]) -> dict[str, str]:
    """
    Given a list of ticker symbols, return a mapping of symbol → full name.

    First checks the AssetMetadata table for cached names, then falls back to
    yfinance for unknown symbols. Returns the symbol itself if resolution fails.
    """
    if not symbols:
        return {}

    unique_symbols = list(set(s.upper() for s in symbols))
    name_map: dict[str, str] = {}

    # Check existing metadata first
    existing = (
        db.query(AssetMetadata)
        .filter(AssetMetadata.symbol.in_(unique_symbols))
        .all()
    )
    for meta in existing:
        if meta.asset_name and meta.asset_name != meta.symbol:
            name_map[meta.symbol] = meta.asset_name

    # Try yfinance for missing ones
    missing = [s for s in unique_symbols if s not in name_map]
    if missing:
        try:
            from app.services.market_data_service import fetch_and_store_metadata
            for symbol in missing:
                try:
                    meta = fetch_and_store_metadata(db, symbol)
                    if meta and meta.asset_name:
                        name_map[symbol] = meta.asset_name
                except Exception:
                    pass
        except Exception:
            pass

    # Fall back to symbol for anything still missing
    for s in unique_symbols:
        if s not in name_map:
            name_map[s] = s

    return name_map
