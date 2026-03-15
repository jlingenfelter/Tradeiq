import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.models.market_data import AssetMetadata
from app.models.analytics import PortfolioSnapshot, AnalyticsSnapshot
from app.services.market_data_service import fetch_quotes, get_benchmark_info
from app.services.warning_service import generate_warnings


def compute_portfolio_analytics(db: Session, portfolio_id: str) -> dict:
    portfolio = db.query(Portfolio).filter(Portfolio.id == uuid.UUID(portfolio_id)).first()
    if not portfolio:
        return {}

    # Gather all positions
    positions = (
        db.query(Position)
        .join(Account)
        .filter(Account.portfolio_id == portfolio.id)
        .all()
    )

    if not positions:
        return _empty_analytics(db, portfolio)

    # Get unique symbols and fetch quotes
    symbols = list(set(p.symbol for p in positions))
    try:
        quotes = fetch_quotes(symbols)
    except Exception:
        quotes = {}

    # Get metadata for sectors/countries — fetch from yfinance if missing
    metadata_map: dict[str, AssetMetadata] = {}
    for sym in symbols:
        meta = db.query(AssetMetadata).filter(AssetMetadata.symbol == sym.upper()).first()
        if not meta:
            try:
                from app.services.market_data_service import fetch_and_store_metadata
                meta = fetch_and_store_metadata(db, sym)
            except Exception:
                pass
        if meta:
            metadata_map[sym] = meta
            # Update position names if they're just the symbol
            for pos in positions:
                if pos.symbol == sym and pos.asset_name == sym and meta.asset_name != sym:
                    pos.asset_name = meta.asset_name
            db.flush()

    # Compute position-level data
    holdings = []
    total_value = 0.0
    total_cost = 0.0

    for pos in positions:
        quote = quotes.get(pos.symbol)
        price = quote.price if quote else 0.0
        prev_close = quote.previous_close if quote else None
        # Fallback: use cost basis per share as price if no market quote
        if price == 0 and pos.cost_basis_per_share:
            price = pos.cost_basis_per_share
        market_value = pos.quantity * price
        cost_basis = pos.cost_basis_total or (pos.cost_basis_per_share or 0) * pos.quantity
        unrealized_pnl = market_value - cost_basis if cost_basis and market_value > 0 else None
        meta = metadata_map.get(pos.symbol)

        holdings.append({
            "symbol": pos.symbol,
            "name": meta.asset_name if meta else pos.asset_name,
            "quantity": pos.quantity,
            "price": price,
            "previous_close": prev_close,
            "market_value": market_value,
            "cost_basis": cost_basis,
            "unrealized_pnl": unrealized_pnl,
            "weight": 0.0,  # computed below
            "sector": meta.sector if meta else None,
            "industry": meta.industry if meta else None,
            "country": meta.country if meta else None,
            "asset_type": meta.asset_type if meta else pos.asset_type,
        })
        total_value += market_value
        total_cost += cost_basis

    # Compute weights
    for h in holdings:
        h["weight"] = (h["market_value"] / total_value * 100) if total_value > 0 else 0.0

    # Sort by weight descending
    holdings.sort(key=lambda x: x["weight"], reverse=True)

    # Concentration metrics
    top_holding_weight = holdings[0]["weight"] if holdings else 0.0
    top_3_weight = sum(h["weight"] for h in holdings[:3])
    top_5_weight = sum(h["weight"] for h in holdings[:5])

    # Sector exposure
    sector_exposure = _compute_allocation(holdings, "sector")
    country_exposure = _compute_allocation(holdings, "country")

    sector_max = max(sector_exposure.values()) if sector_exposure else 0.0
    country_max = max(country_exposure.values()) if country_exposure else 0.0

    # Diversification metrics
    n_sectors = len([s for s in sector_exposure if s != "Unknown"])
    n_countries = len([c for c in country_exposure if c != "Unknown"])
    hhi = sum(h["weight"] ** 2 for h in holdings) / 10000 if holdings else 0.0

    # Health score computation
    health_breakdown = _compute_health_score(
        top_holding_weight, top_3_weight, sector_max, country_max,
        len(holdings), n_sectors, hhi,
    )

    # Stress tests
    stress_tests = _compute_stress_tests(holdings, total_value)

    # Benchmark comparison
    try:
        benchmark = get_benchmark_info("SPY")
    except Exception:
        benchmark = {"symbol": "SPY", "name": "S&P 500", "sector_weights": {}}
    benchmark_comparison = _compute_benchmark_comparison(sector_exposure, benchmark.get("sector_weights", {}))

    # Daily change
    daily_change = 0.0
    for h in holdings:
        if h["previous_close"] and h["previous_close"] > 0:
            daily_change += (h["price"] - h["previous_close"]) * h["quantity"]

    total_unrealized_pnl = total_value - total_cost if total_cost > 0 else None

    # Create snapshots
    portfolio_snapshot = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        total_value=total_value,
        unrealized_pnl=total_unrealized_pnl,
    )
    db.add(portfolio_snapshot)
    db.flush()

    analytics_snapshot = AnalyticsSnapshot(
        portfolio_id=portfolio.id,
        portfolio_snapshot_id=portfolio_snapshot.id,
        health_score=health_breakdown["overall"],
        top_holding_weight=top_holding_weight,
        top_3_weight=top_3_weight,
        top_5_weight=top_5_weight,
        sector_concentration_score=sector_max,
        country_concentration_score=country_max,
        diversification_score=health_breakdown["diversification"],
        sector_exposure=sector_exposure,
        country_exposure=country_exposure,
        stress_tests=stress_tests,
        health_score_breakdown=health_breakdown,
        holdings_detail=[{
            "symbol": h["symbol"],
            "name": h["name"],
            "quantity": h["quantity"],
            "price": h["price"],
            "market_value": round(h["market_value"], 2),
            "weight": round(h["weight"], 2),
            "unrealized_pnl": round(h["unrealized_pnl"], 2) if h["unrealized_pnl"] is not None else None,
            "sector": h["sector"],
            "country": h["country"],
        } for h in holdings],
    )
    db.add(analytics_snapshot)
    db.commit()
    db.refresh(analytics_snapshot)

    # Generate warnings based on the analytics snapshot
    generated_warnings = generate_warnings(db, portfolio_id, str(analytics_snapshot.id))

    return {
        "analytics_snapshot_id": str(analytics_snapshot.id),
        "portfolio_snapshot_id": str(portfolio_snapshot.id),
        "total_value": round(total_value, 2),
        "daily_change": round(daily_change, 2),
        "daily_change_pct": round(daily_change / total_value * 100, 2) if total_value > 0 else 0.0,
        "unrealized_pnl": round(total_unrealized_pnl, 2) if total_unrealized_pnl is not None else None,
        "health_score": health_breakdown["overall"],
        "health_score_breakdown": health_breakdown,
        "top_holding_weight": round(top_holding_weight, 2),
        "top_3_weight": round(top_3_weight, 2),
        "top_5_weight": round(top_5_weight, 2),
        "holdings": holdings,
        "sector_exposure": sector_exposure,
        "country_exposure": country_exposure,
        "stress_tests": stress_tests,
        "benchmark_comparison": benchmark_comparison,
        "position_count": len(holdings),
        "n_sectors": n_sectors,
        "n_countries": n_countries,
        "hhi": round(hhi, 4),
    }


def _compute_allocation(holdings: list[dict], field: str) -> dict[str, float]:
    alloc: dict[str, float] = {}
    for h in holdings:
        key = h.get(field) or "Unknown"
        alloc[key] = alloc.get(key, 0.0) + h["weight"]
    return {k: round(v, 2) for k, v in sorted(alloc.items(), key=lambda x: -x[1])}


def _compute_health_score(
    top_holding_pct: float,
    top_3_pct: float,
    sector_max_pct: float,
    country_max_pct: float,
    n_positions: int,
    n_sectors: int,
    hhi: float,
) -> dict:
    # Single-stock concentration score (25% weight)
    if top_holding_pct <= 5:
        single_stock = 100
    elif top_holding_pct <= 10:
        single_stock = 85
    elif top_holding_pct <= 15:
        single_stock = 65
    elif top_holding_pct <= 20:
        single_stock = 45
    elif top_holding_pct <= 25:
        single_stock = 25
    else:
        single_stock = max(0, 25 - (top_holding_pct - 25) * 2)

    # Sector concentration score (20% weight)
    if sector_max_pct <= 25:
        sector_score = 100
    elif sector_max_pct <= 35:
        sector_score = 75
    elif sector_max_pct <= 45:
        sector_score = 50
    elif sector_max_pct <= 55:
        sector_score = 30
    else:
        sector_score = max(0, 30 - (sector_max_pct - 55) * 2)

    # Diversification score (25% weight)
    position_score = min(100, n_positions * 5) if n_positions < 20 else 100
    sector_div = min(100, n_sectors * 12) if n_sectors < 8 else 100
    hhi_score = max(0, 100 - hhi * 500) if hhi < 0.2 else 0
    diversification = int((position_score + sector_div + hhi_score) / 3)

    # Event risk score (10% weight) - placeholder, full implementation later
    event_risk = 75

    # Benchmark balance (10% weight) - simplified
    benchmark_balance = max(0, 100 - abs(sector_max_pct - 31) * 2)  # 31% is tech in S&P

    # Resilience (10% weight)
    if top_3_pct <= 30:
        resilience = 100
    elif top_3_pct <= 45:
        resilience = 70
    elif top_3_pct <= 60:
        resilience = 40
    else:
        resilience = max(0, 40 - (top_3_pct - 60) * 2)

    overall = int(
        single_stock * 0.25 +
        diversification * 0.25 +
        sector_score * 0.20 +
        event_risk * 0.10 +
        benchmark_balance * 0.10 +
        resilience * 0.10
    )

    return {
        "overall": max(0, min(100, overall)),
        "single_stock_concentration": int(single_stock),
        "diversification": diversification,
        "sector_concentration": int(sector_score),
        "event_risk": event_risk,
        "benchmark_balance": int(benchmark_balance),
        "resilience": int(resilience),
    }


def _compute_stress_tests(holdings: list[dict], total_value: float) -> list[dict]:
    if not holdings or total_value == 0:
        return []

    tests = []

    # Top holding down 10%
    top = holdings[0]
    impact_10 = top["market_value"] * 0.10
    tests.append({
        "scenario": f"{top['symbol']} falls 10%",
        "portfolio_impact_pct": round(-impact_10 / total_value * 100, 2),
        "portfolio_impact_value": round(-impact_10, 2),
        "top_contributors": [{"symbol": top["symbol"], "impact": round(-impact_10, 2)}],
    })

    # Top holding down 20%
    impact_20 = top["market_value"] * 0.20
    tests.append({
        "scenario": f"{top['symbol']} falls 20%",
        "portfolio_impact_pct": round(-impact_20 / total_value * 100, 2),
        "portfolio_impact_value": round(-impact_20, 2),
        "top_contributors": [{"symbol": top["symbol"], "impact": round(-impact_20, 2)}],
    })

    # Top sector down 10%
    sector_holdings = {}
    for h in holdings:
        s = h.get("sector") or "Unknown"
        sector_holdings.setdefault(s, []).append(h)
    if sector_holdings:
        top_sector = max(sector_holdings.items(), key=lambda x: sum(h["market_value"] for h in x[1]))
        sector_name = top_sector[0]
        sector_impact = sum(h["market_value"] for h in top_sector[1]) * 0.10
        contributors = sorted(top_sector[1], key=lambda h: -h["market_value"])[:3]
        tests.append({
            "scenario": f"{sector_name} sector falls 10%",
            "portfolio_impact_pct": round(-sector_impact / total_value * 100, 2),
            "portfolio_impact_value": round(-sector_impact, 2),
            "top_contributors": [{"symbol": c["symbol"], "impact": round(-c["market_value"] * 0.10, 2)} for c in contributors],
        })

    # Overall market down 10%
    market_impact = total_value * 0.10
    top_3_impact = [{"symbol": h["symbol"], "impact": round(-h["market_value"] * 0.10, 2)} for h in holdings[:3]]
    tests.append({
        "scenario": "Overall market falls 10%",
        "portfolio_impact_pct": -10.0,
        "portfolio_impact_value": round(-market_impact, 2),
        "top_contributors": top_3_impact,
    })

    return tests


def _compute_benchmark_comparison(sector_exposure: dict, benchmark_sectors: dict) -> list[dict]:
    all_sectors = set(list(sector_exposure.keys()) + list(benchmark_sectors.keys()))
    comparison = []
    for sector in all_sectors:
        if sector == "Unknown":
            continue
        portfolio_weight = sector_exposure.get(sector, 0.0)
        benchmark_weight = benchmark_sectors.get(sector, 0.0)
        comparison.append({
            "sector": sector,
            "portfolio_weight": round(portfolio_weight, 2),
            "benchmark_weight": round(benchmark_weight, 2),
            "difference": round(portfolio_weight - benchmark_weight, 2),
        })
    comparison.sort(key=lambda x: abs(x["difference"]), reverse=True)
    return comparison


def _empty_analytics(db: Session, portfolio: Portfolio) -> dict:
    ps = PortfolioSnapshot(portfolio_id=portfolio.id, total_value=0.0)
    db.add(ps)
    db.flush()
    analytics = AnalyticsSnapshot(
        portfolio_id=portfolio.id,
        portfolio_snapshot_id=ps.id,
        health_score=0,
        top_holding_weight=0,
        top_3_weight=0,
        top_5_weight=0,
        sector_concentration_score=0,
        country_concentration_score=0,
        diversification_score=0,
        health_score_breakdown={},
        holdings_detail=[],
        sector_exposure={},
        country_exposure={},
        stress_tests=[],
    )
    db.add(analytics)
    db.commit()
    return {"health_score": 0, "total_value": 0, "holdings": []}
