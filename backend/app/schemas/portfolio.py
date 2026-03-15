from datetime import datetime

from pydantic import BaseModel


class PortfolioCreate(BaseModel):
    name: str
    base_currency: str = "USD"


class PortfolioUpdate(BaseModel):
    name: str | None = None
    base_currency: str | None = None


class PortfolioResponse(BaseModel):
    id: str
    name: str
    base_currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountCreate(BaseModel):
    name: str = "Default"
    source_type: str = "manual"


class AccountResponse(BaseModel):
    id: str
    portfolio_id: str
    name: str
    source_type: str
    created_at: datetime

    class Config:
        from_attributes = True
