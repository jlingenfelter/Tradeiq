import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.warning import Warning
from app.models.analytics import AnalyticsSnapshot

# Configurable thresholds
THRESHOLDS = {
    "single_stock_concentration": {
        "info": 10, "medium": 15, "high": 20, "critical": 25,
    },
    "top_3_concentration": {
        "info": 35, "medium": 45, "high": 55, "critical": 65,
    },
    "sector_concentration": {
        "info": 30, "medium": 40, "high": 50, "critical": 60,
    },
    "country_concentration": {
        "info": 50, "medium": 60, "high": 70, "critical": 80,
    },
    "low_diversification": {
        "info": 5, "medium": 3, "high": 2, "critical": 1,
    },
}


def generate_warnings(db: Session, portfolio_id: str, analytics_snapshot_id: str, user_id: uuid.UUID | None = None) -> list[Warning]:
    snapshot = db.query(AnalyticsSnapshot).filter(
        AnalyticsSnapshot.id == uuid.UUID(analytics_snapshot_id)
    ).first()
    if not snapshot:
        return []

    warnings: list[Warning] = []
    pid = uuid.UUID(portfolio_id)

    # Determine user_id from portfolio if not provided
    if not user_id and snapshot.portfolio:
        user_id = snapshot.portfolio.user_id

    # Single-stock concentration
    if snapshot.holdings_detail:
        top = snapshot.holdings_detail[0] if snapshot.holdings_detail else None
        if top:
            weight = top.get("weight", 0)
            severity = _get_severity(weight, THRESHOLDS["single_stock_concentration"])
            if severity:
                warnings.append(Warning(
                    user_id=user_id,
                    portfolio_id=pid,
                    analytics_snapshot_id=snapshot.id,
                    warning_type="single_stock_concentration",
                    severity=severity,
                    title="Single-stock concentration is " + severity,
                    description=f"{top['symbol']} represents {weight:.1f}% of the portfolio.",
                    evidence_json={
                        "symbol": top["symbol"],
                        "weight": round(weight, 2),
                        "market_value": top.get("market_value", 0),
                        "threshold": THRESHOLDS["single_stock_concentration"][severity],
                    },
                ))

    # Top 3 concentration
    top_3 = snapshot.top_3_weight
    severity = _get_severity(top_3, THRESHOLDS["top_3_concentration"])
    if severity:
        top_3_symbols = [h["symbol"] for h in (snapshot.holdings_detail or [])[:3]]
        warnings.append(Warning(
            user_id=user_id,
            portfolio_id=pid,
            analytics_snapshot_id=snapshot.id,
            warning_type="top_3_concentration",
            severity=severity,
            title="Top 3 holdings are heavily concentrated",
            description=f"Your top 3 holdings ({', '.join(top_3_symbols)}) account for {top_3:.1f}% of the portfolio.",
            evidence_json={
                "symbols": top_3_symbols,
                "weight": round(top_3, 2),
                "threshold": THRESHOLDS["top_3_concentration"][severity],
            },
        ))

    # Sector concentration
    sector_exposure = snapshot.sector_exposure or {}
    for sector, weight in sector_exposure.items():
        if sector == "Unknown":
            continue
        severity = _get_severity(weight, THRESHOLDS["sector_concentration"])
        if severity:
            warnings.append(Warning(
                user_id=user_id,
                portfolio_id=pid,
                analytics_snapshot_id=snapshot.id,
                warning_type="sector_concentration",
                severity=severity,
                title=f"{sector} exposure is elevated",
                description=f"{sector} accounts for {weight:.1f}% of the portfolio.",
                evidence_json={
                    "sector": sector,
                    "weight": round(weight, 2),
                    "threshold": THRESHOLDS["sector_concentration"][severity],
                },
            ))
            break  # Only warn on the top sector

    # Country concentration
    country_exposure = snapshot.country_exposure or {}
    for country, weight in country_exposure.items():
        if country == "Unknown":
            continue
        severity = _get_severity(weight, THRESHOLDS["country_concentration"])
        if severity:
            warnings.append(Warning(
                user_id=user_id,
                portfolio_id=pid,
                analytics_snapshot_id=snapshot.id,
                warning_type="country_concentration",
                severity=severity,
                title=f"Heavy concentration in {country}",
                description=f"{country} accounts for {weight:.1f}% of the portfolio.",
                evidence_json={
                    "country": country,
                    "weight": round(weight, 2),
                    "threshold": THRESHOLDS["country_concentration"][severity],
                },
            ))
            break

    # Low diversification
    holdings_count = len(snapshot.holdings_detail or [])
    if holdings_count > 0:
        n_sectors = len([s for s in sector_exposure if s != "Unknown"])
        if n_sectors <= THRESHOLDS["low_diversification"]["critical"]:
            severity = "critical"
        elif n_sectors <= THRESHOLDS["low_diversification"]["high"]:
            severity = "high"
        elif n_sectors <= THRESHOLDS["low_diversification"]["medium"]:
            severity = "medium"
        elif n_sectors <= THRESHOLDS["low_diversification"]["info"]:
            severity = "info"
        else:
            severity = None

        if severity:
            warnings.append(Warning(
                user_id=user_id,
                portfolio_id=pid,
                analytics_snapshot_id=snapshot.id,
                warning_type="low_diversification",
                severity=severity,
                title="Portfolio lacks sector diversification",
                description=f"Portfolio spans only {n_sectors} sector(s) across {holdings_count} positions.",
                evidence_json={
                    "n_sectors": n_sectors,
                    "n_positions": holdings_count,
                },
            ))

    # Save warnings
    for w in warnings:
        db.add(w)
    db.commit()

    return warnings


def _get_severity(value: float, thresholds: dict[str, float]) -> str | None:
    if value >= thresholds["critical"]:
        return "critical"
    elif value >= thresholds["high"]:
        return "high"
    elif value >= thresholds["medium"]:
        return "medium"
    elif value >= thresholds["info"]:
        return "info"
    return None


def get_latest_warnings(db: Session, portfolio_id: uuid.UUID) -> list[Warning]:
    latest_snapshot = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.portfolio_id == portfolio_id)
        .order_by(AnalyticsSnapshot.created_at.desc())
        .first()
    )
    if not latest_snapshot:
        return []

    return (
        db.query(Warning)
        .filter(
            Warning.portfolio_id == portfolio_id,
            Warning.analytics_snapshot_id == latest_snapshot.id,
        )
        .order_by(
            Warning.severity.desc(),
            Warning.triggered_at.desc(),
        )
        .all()
    )
