from datetime import datetime

from pydantic import BaseModel


class WarningResponse(BaseModel):
    id: str
    warning_type: str
    severity: str
    title: str
    description: str
    evidence_json: dict
    triggered_at: datetime

    class Config:
        from_attributes = True
