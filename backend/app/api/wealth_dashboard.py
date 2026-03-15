from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.wealth_service import compute_wealth_snapshot, get_net_worth_history
from app.schemas.wealth import WealthDashboardResponse, AllocationItem, ConcentrationItem, WealthWarning, WealthHealthBreakdown

router = APIRouter(prefix="/dashboard", tags=["wealth-dashboard"])


@router.get("/overview", response_model=WealthDashboardResponse)
def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = compute_wealth_snapshot(db, current_user.id)

    if not data:
        return WealthDashboardResponse(
            base_currency=current_user.base_currency,
            total_assets=0, total_liabilities=0, net_worth=0,
            net_worth_change_30d=None,
            liquid_assets=0, illiquid_assets=0, liquid_net_worth=0,
            cash_value=0, investment_value=0, property_value=0,
            crypto_value=0, business_value=0, pension_value=0,
            other_asset_value=0, debt_value=0,
            allocation=[], top_concentrations=[], top_warnings=[],
            health_score=0,
            health_score_breakdown=WealthHealthBreakdown(
                overall=0, liquidity=0, concentration=0, leverage=0,
                diversification=0, data_freshness=0, public_market_risk=0,
            ),
            ai_summary=None,
        )

    return WealthDashboardResponse(
        base_currency=data["base_currency"],
        total_assets=data["total_assets"],
        total_liabilities=data["total_liabilities"],
        net_worth=data["net_worth"],
        net_worth_change_30d=data.get("net_worth_change_30d"),
        liquid_assets=data["liquid_assets"],
        illiquid_assets=data["illiquid_assets"],
        liquid_net_worth=data["liquid_net_worth"],
        cash_value=data["cash_value"],
        investment_value=data["investment_value"],
        property_value=data["property_value"],
        crypto_value=data["crypto_value"],
        business_value=data["business_value"],
        pension_value=data["pension_value"],
        other_asset_value=data["other_asset_value"],
        debt_value=data["debt_value"],
        allocation=[AllocationItem(**a) for a in data["allocation"]],
        top_concentrations=[ConcentrationItem(**c) for c in data["top_concentrations"]],
        top_warnings=[WealthWarning(**w) for w in data["top_warnings"]],
        health_score=data["health_score"],
        health_score_breakdown=WealthHealthBreakdown(**data["health_score_breakdown"]),
        ai_summary=data.get("ai_summary"),
    )


@router.get("/allocation")
def get_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = compute_wealth_snapshot(db, current_user.id)
    return {
        "asset_class_allocation": data.get("allocation", []),
        "liquidity_allocation": data.get("liquidity_allocations", {}),
        "geography_allocation": data.get("geography_allocations", {}),
        "sector_allocation": data.get("sector_allocations", {}),
        "debt_to_asset_ratio": data.get("debt_to_asset_ratio", 0),
        "debt_to_net_worth_ratio": data.get("debt_to_net_worth_ratio", 0),
        "property_ltv": data.get("property_ltv", 0),
    }


@router.get("/net-worth-history")
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history = get_net_worth_history(db, current_user.id)
    return {"history": history}
