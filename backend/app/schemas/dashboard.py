from pydantic import BaseModel


class TopHolding(BaseModel):
    symbol: str
    name: str
    weight: float
    market_value: float


class SectorExposure(BaseModel):
    sector: str
    weight: float


class CountryExposure(BaseModel):
    country: str
    weight: float


class TopRisk(BaseModel):
    type: str
    severity: str
    title: str
    description: str


class DashboardResponse(BaseModel):
    portfolio_id: str
    portfolio_name: str
    base_currency: str
    total_value: float
    daily_change: float
    daily_change_pct: float
    health_score: int
    health_score_breakdown: dict
    top_risks: list[TopRisk]
    top_holdings: list[TopHolding]
    sector_exposure: list[SectorExposure]
    country_exposure: list[CountryExposure]
    stress_tests: list[dict]
    ai_summary: str | None
