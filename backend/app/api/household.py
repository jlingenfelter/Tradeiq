import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.tier_gate import require_family
from app.models.user import User
from app.services.household_service import (
    create_household,
    invite_member,
    accept_invitation,
    get_household_for_user,
    get_combined_wealth,
    list_household_goals,
    create_household_goal,
    delete_household_goal,
)

router = APIRouter(prefix="/household", tags=["household"])


class InviteRequest(BaseModel):
    email: str


class GoalCreateRequest(BaseModel):
    name: str
    target_amount: float
    target_date: str | None = None
    goal_type: str
    emoji: str = "\U0001f3af"
    currency: str = "USD"


@router.get("")
def get_household(
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Get the current user's household info and members."""
    household = get_household_for_user(db, current_user.id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not part of a household")
    return household


@router.post("")
def create_new_household(
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Create a new household (one per user)."""
    return create_household(db, current_user)


@router.post("/invite")
def invite_to_household(
    body: InviteRequest,
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Invite a member by email."""
    household = get_household_for_user(db, current_user.id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Create a household first")
    return invite_member(db, uuid.UUID(household["id"]), body.email, current_user.id)


@router.post("/accept/{invitation_id}")
def accept_household_invitation(
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept a household invitation (no tier required)."""
    return accept_invitation(db, current_user, invitation_id)


@router.get("/combined")
def get_household_combined_wealth(
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Get combined wealth across all household members."""
    household = get_household_for_user(db, current_user.id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not part of a household")
    return get_combined_wealth(db, uuid.UUID(household["id"]))


@router.get("/goals")
def list_goals(
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """List shared household goals."""
    household = get_household_for_user(db, current_user.id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not part of a household")
    return list_household_goals(db, uuid.UUID(household["id"]))


@router.post("/goals")
def create_goal(
    body: GoalCreateRequest,
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Create a shared household goal."""
    household = get_household_for_user(db, current_user.id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not part of a household")
    data = body.model_dump(exclude_none=True)
    return create_household_goal(db, uuid.UUID(household["id"]), data)


@router.delete("/goals/{goal_id}")
def delete_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Delete a shared household goal."""
    household = get_household_for_user(db, current_user.id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not part of a household")
    return delete_household_goal(db, uuid.UUID(household["id"]), goal_id)
