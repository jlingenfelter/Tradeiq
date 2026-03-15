import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.goal_service import get_goals, create_goal, update_goal, delete_goal

router = APIRouter(prefix="/goals", tags=["goals"])


class GoalCreateRequest(BaseModel):
    name: str
    target_amount: float
    target_date: str | None = None
    goal_type: str = "net_worth"
    currency: str | None = None
    emoji: str = "🎯"
    notes: str | None = None


class GoalUpdateRequest(BaseModel):
    name: str | None = None
    target_amount: float | None = None
    target_date: str | None = None
    goal_type: str | None = None
    currency: str | None = None
    emoji: str | None = None
    notes: str | None = None
    is_active: bool | None = None


@router.get("")
def list_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all active goals with progress data."""
    return get_goals(db, current_user.id)


@router.post("")
def create_new_goal(
    body: GoalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new wealth goal."""
    data = body.model_dump(exclude_none=True)
    return create_goal(db, current_user.id, data)


@router.patch("/{goal_id}")
def update_existing_goal(
    goal_id: uuid.UUID,
    body: GoalUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a goal."""
    data = body.model_dump(exclude_none=True)
    return update_goal(db, current_user.id, goal_id, data)


@router.delete("/{goal_id}")
def delete_existing_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a goal."""
    return delete_goal(db, current_user.id, goal_id)
