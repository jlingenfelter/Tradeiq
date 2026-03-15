from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.smart_alerts_service import generate_smart_alerts

router = APIRouter(prefix="/smart-alerts", tags=["smart-alerts"])


@router.get("")
def get_smart_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alerts = generate_smart_alerts(db, current_user.id)
    return {"alerts": alerts}
