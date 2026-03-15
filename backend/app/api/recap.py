from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.recap_service import generate_weekly_recap

router = APIRouter(prefix="/recap", tags=["recap"])


@router.get("/weekly")
def weekly_recap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a fun weekly wealth recap."""
    recap = generate_weekly_recap(db, current_user.id)
    if not recap:
        return {"message": "Not enough data yet for a recap. Keep tracking!"}
    return recap
