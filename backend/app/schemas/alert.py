from datetime import datetime

from pydantic import BaseModel


class AlertCreate(BaseModel):
    alert_type: str
    threshold_json: dict = {}
    channel: str = "in_app"
    enabled: bool = True


class AlertUpdate(BaseModel):
    threshold_json: dict | None = None
    channel: str | None = None
    enabled: bool | None = None


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    threshold_json: dict
    channel: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True
