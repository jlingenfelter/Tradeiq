"""
Wealth calculation engine — deterministic, auditable calculations for net worth,
allocation, liquidity, concentration, leverage, and health score.

Includes portfolio positions (from broker integrations and CSV imports) as part
of the total wealth picture.
"""
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wealth import (
    Asset, Liability, WealthSnapshot, AllocationSnapshot, WealthContainer,
)
from app.models.portfolio import Portfolio, Account
from app.models.position import Position
from app.models.analytics import PortfolioSnapshot, AnalyticsSnapshot

# ── Liquidity defaults by asset_class ──
LIQUIDITY_DEFAULTS = {
    "cash": "highly_liquid",
    "stock": "liquid",
    "etf": "liquid",
    "mutual_fund": "liquid",
    "bond": "semi_liquid",
    "pension": "semi_liquid",
    "crypto": "liquid",
    "property": "illiquid",
    "business_equity": "illiquid",
    "gold": "semi_liquid",
    "watch": "illiquid",
    "collectible": "illiquid",
    "private_loan_receivable": "illiquid",
    "other": "semi_liquid",
}

# ── Asset class to display category mapping ──
ASSET_CLASS_CATEGORIES = {
    "cash": "Cash",
    "stock": "Public Investments",
    "etf": "Public Investments",
    "mutual_fund": "Public Investments",
    "bond": "Public Investments",
    "pension": "Pensions",
    "crypto": "Crypto",
    "property": "Property",
    "business_equity": "Business Equity",
    "gold": "Alternatives",
    "watch": "Alternatives",
    "collectible": "Alternatives",
    "private_loan_receivable": "Other",
    "other": "Other",
}

LIQUID_CATEGORIES = {"highly_liquid", "liquid"}
ILLIQUID_CATEGORIES = {"semi_liquid", "illiquid"}


def _get_portfolio_asset_details(db: Session, user_id: uuid.UUID) -> list[dict]:
    """
    Pull all portfolio positions for a user and convert them into asset_detail dicts
    that can be mixed into the wealth calculation. Uses the latest analytics snapshot
    for market values; falls back to cost basis if no analytics available.
    """
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    if not portfolios:
        return []

    details = []
    for portfolio in portfolios:
        # Try to get holdings from the latest analytics snapshot
        latest_analytics = (
            db.query(AnalyticsSnapshot)
            .filter(AnalyticsSnapshot.portfolio_id == portfolio.id)
            .order_by(AnalyticsSnapshot.created_at.desc())
            .first()
        )

        holdings_map: dict[str, dict] = {}
        if latest_analytics and latest_analytics.holdings_detail:
            for h in latest_analytics.holdings_detail:
                holdings_map[h.get("symbol", "")] = h

        # Get all positions across all accounts in this portfolio
        positions = (
            db.query(Position)
            .join(Account)
            .filter(Account.portfolio_id == portfolio.id)
            .all()
        )

        for pos in positions:
            h = holdings_map.get(pos.symbol, {})
            market_value = h.get("market_value") or 0
            # Fallback: use cost basis if no market value from analytics
            if market_value == 0:
                market_value = pos.cost_basis_total or (
                    (pos.cost_basis_per_share or 0) * pos.quantity
                )

            price = h.get("price", 0)
            sector = h.get("sector")
            country = h.get("country")
            asset_type = h.get("asset_type", pos.asset_type)

            # Map position asset_type to wealth asset_class
            if asset_type in ("crypto", "cryptocurrency"):
                asset_class = "crypto"
            elif asset_type in ("etf", "ETF"):
                asset_class = "etf"
            elif asset_type in ("mutual_fund",):
                asset_class = "mutual_fund"
            elif asset_type in ("bond",):
                asset_class = "bond"
            else:
                asset_class = "stock"

            category = ASSET_CLASS_CATEGORIES.get(asset_class, "Public Investments")
            liq = LIQUIDITY_DEFAULTS.get(asset_class, "liquid")

            details.append({
                "id": str(pos.id),
                "name": pos.asset_name,
                "symbol": pos.symbol,
                "asset_class": asset_class,
                "category": category,
                "value": round(market_value, 2),
                "currency": pos.currency,
                "liquidity": liq,
                "country": country,
                "sector": sector,
                "valuation_date": (pos.last_synced_at or pos.updated_at).isoformat() if (pos.last_synced_at or pos.updated_at) else None,
                "valuation_source": "market",
                "source": "portfolio",  # tag so we know it came from positions
                "portfolio_name": portfolio.name,
            })

    return details


def compute_wealth_snapshot(db: Session, user_id: uuid.UUID) -> dict:
    """Compute full wealth snapshot for a user, including portfolio positions."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}

    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    liabilities_list = db.query(Liability).filter(Liability.user_id == user_id).all()

    # ── Compute totals ──
    total_assets = 0.0
    liquid_assets = 0.0
    illiquid_assets = 0.0
    cash_value = 0.0
    investment_value = 0.0
    property_value = 0.0
    crypto_value = 0.0
    business_value = 0.0
    pension_value = 0.0
    other_asset_value = 0.0

    asset_details = []
    for a in assets:
        val = a.current_value * (a.ownership_pct or 100.0) / 100.0
        total_assets += val

        liq = a.liquidity_category or LIQUIDITY_DEFAULTS.get(a.asset_class, "semi_liquid")
        if liq in LIQUID_CATEGORIES:
            liquid_assets += val
        else:
            illiquid_assets += val

        category = ASSET_CLASS_CATEGORIES.get(a.asset_class, "Other")
        if category == "Cash":
            cash_value += val
        elif category == "Public Investments":
            investment_value += val
        elif category == "Property":
            property_value += val
        elif category == "Crypto":
            crypto_value += val
        elif category == "Business Equity":
            business_value += val
        elif category == "Pensions":
            pension_value += val
        else:
            other_asset_value += val

        asset_details.append({
            "id": str(a.id),
            "name": a.name,
            "asset_class": a.asset_class,
            "category": category,
            "value": round(val, 2),
            "currency": a.currency,
            "liquidity": liq,
            "country": a.country,
            "sector": a.sector,
            "valuation_date": a.valuation_date.isoformat() if a.valuation_date else None,
            "valuation_source": a.valuation_source,
        })

    # ── Include portfolio positions (broker/CSV imports) ──
    try:
        portfolio_details = _get_portfolio_asset_details(db, user_id)
        for pd in portfolio_details:
            val = pd["value"]
            if val <= 0:
                continue
            total_assets += val

            liq = pd["liquidity"]
            if liq in LIQUID_CATEGORIES:
                liquid_assets += val
            else:
                illiquid_assets += val

            category = pd["category"]
            if category == "Cash":
                cash_value += val
            elif category == "Public Investments":
                investment_value += val
            elif category == "Property":
                property_value += val
            elif category == "Crypto":
                crypto_value += val
            elif category == "Business Equity":
                business_value += val
            elif category == "Pensions":
                pension_value += val
            else:
                other_asset_value += val

            asset_details.append(pd)
    except Exception as e:
        import traceback
        print(f"[wealth_service] Error bridging portfolio positions: {e}\n{traceback.format_exc()}")

    total_liabilities = sum(l.current_balance for l in liabilities_list)
    net_worth = total_assets - total_liabilities
    liquid_net_worth = liquid_assets - total_liabilities

    # ── Allocation by asset class ──
    allocation_by_class: dict[str, float] = {}
    for ad in asset_details:
        cat = ad["category"]
        allocation_by_class[cat] = allocation_by_class.get(cat, 0.0) + ad["value"]

    allocation = []
    for cat, val in sorted(allocation_by_class.items(), key=lambda x: -x[1]):
        weight = (val / total_assets * 100) if total_assets > 0 else 0.0
        allocation.append({"category": cat, "value": round(val, 2), "weight": round(weight, 2)})

    # ── Liquidity allocation ──
    liquidity_alloc = {
        "highly_liquid": 0.0,
        "liquid": 0.0,
        "semi_liquid": 0.0,
        "illiquid": 0.0,
    }
    for ad in asset_details:
        liquidity_alloc[ad["liquidity"]] = liquidity_alloc.get(ad["liquidity"], 0.0) + ad["value"]

    # ── Top concentrations ──
    asset_details.sort(key=lambda x: -x["value"])
    top_concentrations = []
    for ad in asset_details[:5]:
        w = (ad["value"] / total_assets * 100) if total_assets > 0 else 0.0
        top_concentrations.append({
            "label": ad["name"],
            "value": ad["value"],
            "weight_of_assets": round(w, 2),
        })

    # ── Geography allocation ──
    geo_alloc: dict[str, float] = {}
    for ad in asset_details:
        c = ad.get("country") or "Unknown"
        geo_alloc[c] = geo_alloc.get(c, 0.0) + ad["value"]

    # ── Sector allocation (for public investments) ──
    sector_alloc: dict[str, float] = {}
    for ad in asset_details:
        if ad["category"] == "Public Investments" and ad.get("sector"):
            sector_alloc[ad["sector"]] = sector_alloc.get(ad["sector"], 0.0) + ad["value"]

    # ── Debt metrics ──
    debt_to_asset = (total_liabilities / total_assets * 100) if total_assets > 0 else 0.0
    debt_to_net_worth = (total_liabilities / net_worth * 100) if net_worth > 0 else 0.0

    # Property-specific debt
    property_debt = sum(
        l.current_balance for l in liabilities_list
        if l.liability_type == "mortgage"
    )
    property_ltv = (property_debt / property_value * 100) if property_value > 0 else 0.0

    # ── Health score ──
    health_breakdown = _compute_wealth_health_score(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        liquid_assets=liquid_assets,
        illiquid_assets=illiquid_assets,
        asset_details=asset_details,
        allocation=allocation,
        assets=assets,
    )

    # ── Warnings ──
    warnings = _generate_wealth_warnings(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        liquid_assets=liquid_assets,
        illiquid_assets=illiquid_assets,
        net_worth=net_worth,
        allocation_by_class=allocation_by_class,
        asset_details=asset_details,
        debt_to_asset=debt_to_asset,
        property_ltv=property_ltv,
        assets=assets,
    )

    # ── Get previous snapshot for change calculation ──
    prev_snapshot = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .first()
    )
    net_worth_change_30d = None
    if prev_snapshot:
        net_worth_change_30d = round(net_worth - prev_snapshot.net_worth, 2)

    # ── Save snapshot ──
    ws = WealthSnapshot(
        user_id=user_id,
        total_assets=round(total_assets, 2),
        total_liabilities=round(total_liabilities, 2),
        net_worth=round(net_worth, 2),
        liquid_assets=round(liquid_assets, 2),
        illiquid_assets=round(illiquid_assets, 2),
        liquid_net_worth=round(liquid_net_worth, 2),
        cash_value=round(cash_value, 2),
        investment_value=round(investment_value, 2),
        property_value=round(property_value, 2),
        crypto_value=round(crypto_value, 2),
        business_value=round(business_value, 2),
        pension_value=round(pension_value, 2),
        other_asset_value=round(other_asset_value, 2),
        debt_value=round(total_liabilities, 2),
    )
    db.add(ws)
    db.flush()

    alloc_snap = AllocationSnapshot(
        user_id=user_id,
        wealth_snapshot_id=ws.id,
        asset_class_allocations_json=allocation,
        liquidity_allocations_json=liquidity_alloc,
        geography_allocations_json=geo_alloc,
        sector_allocations_json=sector_alloc,
        top_concentrations_json=top_concentrations,
        health_score=health_breakdown["overall"],
        health_score_breakdown_json=health_breakdown,
        warnings_json=[{
            "severity": w["severity"],
            "title": w["title"],
            "description": w["description"],
            "warning_type": w["warning_type"],
        } for w in warnings],
    )
    db.add(alloc_snap)
    db.commit()

    return {
        "base_currency": user.base_currency,
        "total_assets": round(total_assets, 2),
        "total_liabilities": round(total_liabilities, 2),
        "net_worth": round(net_worth, 2),
        "net_worth_change_30d": net_worth_change_30d,
        "liquid_assets": round(liquid_assets, 2),
        "illiquid_assets": round(illiquid_assets, 2),
        "liquid_net_worth": round(liquid_net_worth, 2),
        "cash_value": round(cash_value, 2),
        "investment_value": round(investment_value, 2),
        "property_value": round(property_value, 2),
        "crypto_value": round(crypto_value, 2),
        "business_value": round(business_value, 2),
        "pension_value": round(pension_value, 2),
        "other_asset_value": round(other_asset_value, 2),
        "debt_value": round(total_liabilities, 2),
        "allocation": allocation,
        "top_concentrations": top_concentrations,
        "top_warnings": warnings[:5],
        "health_score": health_breakdown["overall"],
        "health_score_breakdown": health_breakdown,
        "ai_summary": None,
        "debt_to_asset_ratio": round(debt_to_asset, 2),
        "debt_to_net_worth_ratio": round(debt_to_net_worth, 2),
        "property_ltv": round(property_ltv, 2),
        "liquidity_allocations": liquidity_alloc,
        "geography_allocations": geo_alloc,
        "sector_allocations": sector_alloc,
    }


def get_net_worth_history(db: Session, user_id: uuid.UUID, limit: int = 90) -> list[dict]:
    """Get historical net worth snapshots."""
    snapshots = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "date": s.snapshot_time.isoformat(),
            "total_assets": s.total_assets,
            "total_liabilities": s.total_liabilities,
            "net_worth": s.net_worth,
            "liquid_assets": s.liquid_assets,
        }
        for s in reversed(snapshots)
    ]


def _compute_wealth_health_score(
    total_assets: float,
    total_liabilities: float,
    liquid_assets: float,
    illiquid_assets: float,
    asset_details: list[dict],
    allocation: list[dict],
    assets: list,
) -> dict:
    """
    Wealth health score: 0-100.
    Components: liquidity(25%), concentration(20%), leverage(20%),
    diversification(20%), data_freshness(5%), public_market_risk(10%)
    """
    # ── Liquidity score (25%) ──
    if total_assets == 0:
        liquidity_score = 0
    else:
        liquid_pct = liquid_assets / total_assets * 100
        if liquid_pct >= 40:
            liquidity_score = 100
        elif liquid_pct >= 30:
            liquidity_score = 80
        elif liquid_pct >= 20:
            liquidity_score = 60
        elif liquid_pct >= 10:
            liquidity_score = 40
        else:
            liquidity_score = max(0, int(liquid_pct * 4))

    # ── Concentration score (20%) ──
    if not asset_details or total_assets == 0:
        concentration_score = 100
    else:
        top_weight = asset_details[0]["value"] / total_assets * 100 if asset_details else 0
        if top_weight <= 15:
            concentration_score = 100
        elif top_weight <= 25:
            concentration_score = 75
        elif top_weight <= 35:
            concentration_score = 50
        elif top_weight <= 50:
            concentration_score = 30
        else:
            concentration_score = max(0, 30 - int((top_weight - 50) * 1.5))

    # ── Leverage score (20%) ──
    if total_assets == 0:
        leverage_score = 100
    else:
        debt_ratio = total_liabilities / total_assets * 100
        if debt_ratio <= 10:
            leverage_score = 100
        elif debt_ratio <= 25:
            leverage_score = 80
        elif debt_ratio <= 40:
            leverage_score = 55
        elif debt_ratio <= 60:
            leverage_score = 30
        else:
            leverage_score = max(0, 30 - int((debt_ratio - 60) * 1.5))

    # ── Diversification score (20%) ──
    n_categories = len([a for a in allocation if a["weight"] > 1])
    if n_categories >= 5:
        diversification_score = 100
    elif n_categories >= 4:
        diversification_score = 80
    elif n_categories >= 3:
        diversification_score = 60
    elif n_categories >= 2:
        diversification_score = 35
    else:
        diversification_score = 10

    # ── Data freshness score (5%) ──
    now = datetime.now(timezone.utc)
    stale_count = 0
    for a in assets:
        if a.valuation_source == "manual" and a.valuation_date:
            age = (now - a.valuation_date.replace(tzinfo=timezone.utc) if a.valuation_date.tzinfo is None else now - a.valuation_date)
            if age > timedelta(days=90):
                stale_count += 1
    total_count = len(assets) or 1
    fresh_pct = (1 - stale_count / total_count) * 100
    data_freshness = int(fresh_pct)

    # ── Public market risk score (10%) ──
    # Based on investment concentration within total wealth
    inv_weight = 0
    for a in allocation:
        if a["category"] == "Public Investments":
            inv_weight = a["weight"]
    if inv_weight <= 50:
        public_market_risk = 100
    elif inv_weight <= 70:
        public_market_risk = 70
    elif inv_weight <= 85:
        public_market_risk = 40
    else:
        public_market_risk = 20

    overall = int(
        liquidity_score * 0.25 +
        concentration_score * 0.20 +
        leverage_score * 0.20 +
        diversification_score * 0.20 +
        data_freshness * 0.05 +
        public_market_risk * 0.10
    )

    return {
        "overall": max(0, min(100, overall)),
        "liquidity": int(liquidity_score),
        "concentration": int(concentration_score),
        "leverage": int(leverage_score),
        "diversification": int(diversification_score),
        "data_freshness": int(data_freshness),
        "public_market_risk": int(public_market_risk),
    }


def _generate_wealth_warnings(
    total_assets: float,
    total_liabilities: float,
    liquid_assets: float,
    illiquid_assets: float,
    net_worth: float,
    allocation_by_class: dict[str, float],
    asset_details: list[dict],
    debt_to_asset: float,
    property_ltv: float,
    assets: list,
) -> list[dict]:
    """Generate wealth-level warnings."""
    warnings = []

    if total_assets == 0:
        return warnings

    # ── Single asset concentration ──
    if asset_details:
        top = asset_details[0]
        top_pct = top["value"] / total_assets * 100
        severity = _threshold_check(top_pct, [("critical", 50), ("high", 35), ("medium", 25), ("info", 15)])
        if severity:
            warnings.append({
                "warning_type": "single_asset_concentration",
                "severity": severity,
                "title": f"High concentration in {top['name']}",
                "description": f"{top['name']} represents {top_pct:.1f}% of total assets.",
                "evidence": {"asset": top["name"], "pct": round(top_pct, 1)},
            })

    # ── Property concentration ──
    prop_val = allocation_by_class.get("Property", 0)
    if prop_val > 0:
        prop_pct = prop_val / total_assets * 100
        severity = _threshold_check(prop_pct, [("critical", 70), ("high", 55), ("medium", 40)])
        if severity:
            warnings.append({
                "warning_type": "property_concentration",
                "severity": severity,
                "title": "Property concentration is elevated",
                "description": f"Property accounts for {prop_pct:.1f}% of total assets.",
                "evidence": {"property_value": round(prop_val, 2), "pct": round(prop_pct, 1)},
            })

    # ── Crypto concentration ──
    crypto_val = allocation_by_class.get("Crypto", 0)
    if crypto_val > 0:
        crypto_pct = crypto_val / total_assets * 100
        severity = _threshold_check(crypto_pct, [("critical", 35), ("high", 20), ("medium", 10)])
        if severity:
            warnings.append({
                "warning_type": "crypto_concentration",
                "severity": severity,
                "title": "Crypto allocation is notable",
                "description": f"Crypto accounts for {crypto_pct:.1f}% of total assets.",
                "evidence": {"crypto_value": round(crypto_val, 2), "pct": round(crypto_pct, 1)},
            })

    # ── Illiquidity ──
    illiquid_pct = illiquid_assets / total_assets * 100 if total_assets > 0 else 0
    severity = _threshold_check(illiquid_pct, [("critical", 80), ("high", 65), ("medium", 50)])
    if severity:
        warnings.append({
            "warning_type": "illiquid_asset_concentration",
            "severity": severity,
            "title": "Illiquid assets dominate total wealth",
            "description": f"{illiquid_pct:.1f}% of total assets are classified as semi-liquid or illiquid.",
            "evidence": {"illiquid_assets": round(illiquid_assets, 2), "pct": round(illiquid_pct, 1)},
        })

    # ── Leverage ──
    severity = _threshold_check(debt_to_asset, [("critical", 60), ("high", 40), ("medium", 25)])
    if severity:
        warnings.append({
            "warning_type": "leverage_elevated",
            "severity": severity,
            "title": "Debt-to-asset ratio is elevated",
            "description": f"Liabilities represent {debt_to_asset:.1f}% of total assets.",
            "evidence": {"debt_to_asset_pct": round(debt_to_asset, 1)},
        })

    # ── Low liquidity vs liabilities ──
    if total_liabilities > 0 and liquid_assets < total_liabilities * 0.5:
        warnings.append({
            "warning_type": "low_liquidity_vs_debt",
            "severity": "high",
            "title": "Liquid assets are low relative to liabilities",
            "description": f"Liquid assets ({liquid_assets:,.0f}) are less than half of total liabilities ({total_liabilities:,.0f}).",
            "evidence": {"liquid_assets": round(liquid_assets, 2), "total_liabilities": round(total_liabilities, 2)},
        })

    # ── Business equity concentration ──
    biz_val = allocation_by_class.get("Business Equity", 0)
    if biz_val > 0:
        biz_pct = biz_val / total_assets * 100
        severity = _threshold_check(biz_pct, [("critical", 60), ("high", 40), ("medium", 25)])
        if severity:
            warnings.append({
                "warning_type": "business_concentration",
                "severity": severity,
                "title": "Business equity concentration is high",
                "description": f"Business interests account for {biz_pct:.1f}% of total assets.",
                "evidence": {"business_value": round(biz_val, 2), "pct": round(biz_pct, 1)},
            })

    # ── Stale valuations ──
    now = datetime.now(timezone.utc)
    stale_assets = []
    for a in assets:
        if a.valuation_source in ("manual", "estimated") and a.valuation_date:
            vd = a.valuation_date.replace(tzinfo=timezone.utc) if a.valuation_date.tzinfo is None else a.valuation_date
            if (now - vd) > timedelta(days=90):
                stale_assets.append(a.name)
    if stale_assets:
        warnings.append({
            "warning_type": "stale_valuation",
            "severity": "medium" if len(stale_assets) <= 2 else "high",
            "title": f"{len(stale_assets)} asset(s) have stale valuations",
            "description": f"The following assets haven't been updated in over 90 days: {', '.join(stale_assets[:5])}.",
            "evidence": {"stale_assets": stale_assets[:10], "count": len(stale_assets)},
        })

    # ── High property LTV ──
    if property_ltv > 80:
        warnings.append({
            "warning_type": "high_property_ltv",
            "severity": "high" if property_ltv > 90 else "medium",
            "title": "Property loan-to-value is high",
            "description": f"Mortgage debt is {property_ltv:.1f}% of property value.",
            "evidence": {"ltv_pct": round(property_ltv, 1)},
        })

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "info": 3}
    warnings.sort(key=lambda w: severity_order.get(w["severity"], 4))

    return warnings


def _threshold_check(value: float, thresholds: list[tuple[str, float]]) -> str | None:
    """Check value against descending thresholds. Returns first matching severity."""
    for severity, threshold in thresholds:
        if value >= threshold:
            return severity
    return None
