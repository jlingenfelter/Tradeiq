from pydantic import BaseModel


class HealthScoreBreakdown(BaseModel):
    overall: int
    single_stock_concentration: int
    diversification: int
    sector_concentration: int
    event_risk: int
    benchmark_balance: int
    resilience: int


class StressTestResult(BaseModel):
    scenario: str
    portfolio_impact_pct: float
    portfolio_impact_value: float
    top_contributors: list[dict]


class HoldingDetail(BaseModel):
    symbol: str
    name: str
    quantity: float
    price: float
    market_value: float
    weight: float
    unrealized_pnl: float | None
    sector: str | None
    country: str | None


class BenchmarkComparison(BaseModel):
    sector: str
    portfolio_weight: float
    benchmark_weight: float
    difference: float


class AnalyticsResponse(BaseModel):
    analytics_snapshot_id: str
    portfolio_snapshot_id: str
    total_value: float
    daily_change: float
    daily_change_pct: float
    unrealized_pnl: float | None
    health_score: int
    health_score_breakdown: HealthScoreBreakdown
    top_holding_weight: float
    top_3_weight: float
    top_5_weight: float
    holdings: list[HoldingDetail]
    sector_exposure: dict[str, float]
    country_exposure: dict[str, float]
    stress_tests: list[StressTestResult]
    benchmark_comparison: list[BenchmarkComparison]
    position_count: int
    n_sectors: int
    n_countries: int
    hhi: float
