from datetime import datetime

from pydantic import BaseModel


class PositionCreate(BaseModel):
    symbol: str
    asset_name: str
    asset_type: str = "equity"
    quantity: float
    cost_basis_total: float | None = None
    cost_basis_per_share: float | None = None
    currency: str = "USD"
    account_id: str | None = None


class PositionUpdate(BaseModel):
    quantity: float | None = None
    cost_basis_total: float | None = None
    cost_basis_per_share: float | None = None


class PositionResponse(BaseModel):
    id: str
    account_id: str
    symbol: str
    asset_name: str
    asset_type: str
    quantity: float
    cost_basis_total: float | None
    cost_basis_per_share: float | None
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class CsvUploadResponse(BaseModel):
    preview: list[dict]
    columns: list[str]
    row_count: int
    upload_id: str


class CsvConfirmRequest(BaseModel):
    upload_id: str
    column_mapping: dict[str, str]  # csv_column -> field_name
    account_name: str = "CSV Import"


class CsvImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
