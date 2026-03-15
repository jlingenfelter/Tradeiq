from datetime import datetime
from pydantic import BaseModel


# ── WealthContainer ──

class ContainerCreate(BaseModel):
    name: str
    container_type: str
    institution_name: str | None = None
    currency: str = "USD"


class ContainerUpdate(BaseModel):
    name: str | None = None
    container_type: str | None = None
    institution_name: str | None = None
    currency: str | None = None


class ContainerResponse(BaseModel):
    id: str
    name: str
    container_type: str
    institution_name: str | None
    currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Asset ──

class AssetCreate(BaseModel):
    container_id: str | None = None
    asset_class: str
    asset_subclass: str | None = None
    name: str
    symbol: str | None = None
    quantity: float | None = None
    unit_value: float | None = None
    current_value: float
    cost_basis: float | None = None
    currency: str = "USD"
    ownership_pct: float | None = 100.0
    liquidity_category: str = "liquid"
    valuation_source: str = "manual"
    country: str | None = None
    sector: str | None = None
    notes: str | None = None
    metadata_json: dict | None = None


class AssetUpdate(BaseModel):
    container_id: str | None = None
    asset_class: str | None = None
    asset_subclass: str | None = None
    name: str | None = None
    symbol: str | None = None
    quantity: float | None = None
    unit_value: float | None = None
    current_value: float | None = None
    cost_basis: float | None = None
    currency: str | None = None
    ownership_pct: float | None = None
    liquidity_category: str | None = None
    valuation_source: str | None = None
    country: str | None = None
    sector: str | None = None
    notes: str | None = None
    metadata_json: dict | None = None


class AssetResponse(BaseModel):
    id: str
    container_id: str | None
    asset_class: str
    asset_subclass: str | None
    name: str
    symbol: str | None
    quantity: float | None
    unit_value: float | None
    current_value: float
    cost_basis: float | None
    currency: str
    ownership_pct: float | None
    liquidity_category: str
    valuation_source: str
    valuation_date: datetime
    country: str | None
    sector: str | None
    notes: str | None
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Liability ──

class LiabilityCreate(BaseModel):
    container_id: str | None = None
    liability_type: str
    name: str
    current_balance: float
    currency: str = "USD"
    interest_rate: float | None = None
    monthly_payment: float | None = None
    due_date: datetime | None = None
    linked_asset_id: str | None = None
    notes: str | None = None


class LiabilityUpdate(BaseModel):
    container_id: str | None = None
    liability_type: str | None = None
    name: str | None = None
    current_balance: float | None = None
    currency: str | None = None
    interest_rate: float | None = None
    monthly_payment: float | None = None
    due_date: datetime | None = None
    linked_asset_id: str | None = None
    notes: str | None = None


class LiabilityResponse(BaseModel):
    id: str
    container_id: str | None
    liability_type: str
    name: str
    current_balance: float
    currency: str
    interest_rate: float | None
    monthly_payment: float | None
    due_date: datetime | None
    linked_asset_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Wealth Dashboard ──

class AllocationItem(BaseModel):
    category: str
    value: float
    weight: float


class ConcentrationItem(BaseModel):
    label: str
    value: float
    weight_of_assets: float


class WealthWarning(BaseModel):
    severity: str
    title: str
    description: str
    warning_type: str | None = None
    evidence: dict | None = None


class WealthHealthBreakdown(BaseModel):
    overall: int
    liquidity: int
    concentration: int
    leverage: int
    diversification: int
    data_freshness: int
    public_market_risk: int


class WealthHolding(BaseModel):
    name: str
    symbol: str | None = None
    category: str
    asset_class: str
    value: float
    weight: float
    currency: str = "USD"
    country: str | None = None
    sector: str | None = None
    source: str = "manual"


class WealthDashboardResponse(BaseModel):
    base_currency: str
    total_assets: float
    total_liabilities: float
    net_worth: float
    net_worth_change_30d: float | None
    liquid_assets: float
    illiquid_assets: float
    liquid_net_worth: float
    cash_value: float
    investment_value: float
    property_value: float
    crypto_value: float
    business_value: float
    pension_value: float
    other_asset_value: float
    debt_value: float
    allocation: list[AllocationItem]
    top_concentrations: list[ConcentrationItem]
    top_warnings: list[WealthWarning]
    health_score: int
    health_score_breakdown: WealthHealthBreakdown
    ai_summary: str | None
    holdings: list[WealthHolding] = []


class NetWorthHistoryItem(BaseModel):
    date: str
    total_assets: float
    total_liabilities: float
    net_worth: float
    liquid_assets: float


class WealthSnapshotResponse(BaseModel):
    id: str
    snapshot_time: datetime
    total_assets: float
    total_liabilities: float
    net_worth: float
    liquid_assets: float
    illiquid_assets: float
    liquid_net_worth: float
    cash_value: float
    investment_value: float
    property_value: float
    crypto_value: float
    business_value: float
    pension_value: float
    other_asset_value: float
    debt_value: float
