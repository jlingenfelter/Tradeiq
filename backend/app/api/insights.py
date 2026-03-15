from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.insights_service import generate_insights

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("")
def get_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    insights = generate_insights(db, current_user.id)
    return {"insights": insights}
