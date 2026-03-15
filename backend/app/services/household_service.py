"""Household / Family sharing — create household, invite members, combined wealth."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.household import Household, HouseholdMember, HouseholdGoal
from app.models.wealth import WealthSnapshot
from app.models.user import User


def create_household(db: Session, user: User) -> dict:
    """Create a new household owned by the given user. One household per user."""
    existing = db.query(HouseholdMember).filter(
        HouseholdMember.user_id == user.id,
        HouseholdMember.status == "accepted",
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of a household.",
        )

    household = Household(owner_id=user.id, name="My Household")
    db.add(household)
    db.flush()

    # Add the owner as an accepted member
    owner_member = HouseholdMember(
        household_id=household.id,
        user_id=user.id,
        email=user.email,
        role="owner",
        status="accepted",
        accepted_at=datetime.now(timezone.utc),
    )
    db.add(owner_member)
    db.commit()
    db.refresh(household)

    return _household_to_dict(household)


def invite_member(db: Session, household_id: uuid.UUID, email: str, inviter_user_id: uuid.UUID) -> dict:
    """Invite a new member by email."""
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    if household.owner_id != inviter_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the household owner can invite members")

    # Check if already invited
    existing = db.query(HouseholdMember).filter(
        HouseholdMember.household_id == household_id,
        HouseholdMember.email == email,
        HouseholdMember.status.in_(["pending", "accepted"]),
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This email has already been invited")

    member = HouseholdMember(
        household_id=household_id,
        email=email,
        role="member",
        status="pending",
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return _member_to_dict(member)


def accept_invitation(db: Session, user: User, invitation_id: uuid.UUID) -> dict:
    """Accept a pending invitation."""
    invitation = db.query(HouseholdMember).filter(
        HouseholdMember.id == invitation_id,
        HouseholdMember.email == user.email,
        HouseholdMember.status == "pending",
    ).first()
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or already handled")

    # Check if user is already in a household
    existing = db.query(HouseholdMember).filter(
        HouseholdMember.user_id == user.id,
        HouseholdMember.status == "accepted",
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of a household. Leave your current household first.",
        )

    invitation.user_id = user.id
    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invitation)

    return _member_to_dict(invitation)


def get_household_for_user(db: Session, user_id: uuid.UUID) -> dict | None:
    """Get the household a user belongs to, with all members."""
    membership = db.query(HouseholdMember).filter(
        HouseholdMember.user_id == user_id,
        HouseholdMember.status == "accepted",
    ).first()
    if not membership:
        return None

    household = db.query(Household).filter(Household.id == membership.household_id).first()
    if not household:
        return None

    return _household_to_dict(household)


def get_combined_wealth(db: Session, household_id: uuid.UUID) -> dict:
    """Aggregate the latest WealthSnapshot from each accepted household member."""
    members = db.query(HouseholdMember).filter(
        HouseholdMember.household_id == household_id,
        HouseholdMember.status == "accepted",
        HouseholdMember.user_id.isnot(None),
    ).all()

    total_assets = 0.0
    total_liabilities = 0.0
    net_worth = 0.0
    member_snapshots = []

    for member in members:
        latest = (
            db.query(WealthSnapshot)
            .filter(WealthSnapshot.user_id == member.user_id)
            .order_by(WealthSnapshot.snapshot_time.desc())
            .first()
        )
        if latest:
            total_assets += latest.total_assets
            total_liabilities += latest.total_liabilities
            net_worth += latest.net_worth
            member_snapshots.append({
                "user_id": str(member.user_id),
                "email": member.email,
                "net_worth": round(latest.net_worth, 2),
                "total_assets": round(latest.total_assets, 2),
                "total_liabilities": round(latest.total_liabilities, 2),
                "snapshot_time": latest.snapshot_time.isoformat(),
            })

    return {
        "combined_net_worth": round(net_worth, 2),
        "combined_total_assets": round(total_assets, 2),
        "combined_total_liabilities": round(total_liabilities, 2),
        "member_count": len(members),
        "members": member_snapshots,
    }


def list_household_goals(db: Session, household_id: uuid.UUID) -> list[dict]:
    """List all shared goals for a household."""
    goals = db.query(HouseholdGoal).filter(
        HouseholdGoal.household_id == household_id,
    ).order_by(HouseholdGoal.created_at.desc()).all()

    return [_goal_to_dict(g) for g in goals]


def create_household_goal(db: Session, household_id: uuid.UUID, data: dict) -> dict:
    """Create a new shared household goal."""
    goal = HouseholdGoal(
        household_id=household_id,
        name=data["name"],
        target_amount=data["target_amount"],
        target_date=data.get("target_date"),
        goal_type=data["goal_type"],
        currency=data.get("currency", "USD"),
        emoji=data.get("emoji", "\U0001f3af"),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _goal_to_dict(goal)


def delete_household_goal(db: Session, household_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
    """Delete a household goal."""
    goal = db.query(HouseholdGoal).filter(
        HouseholdGoal.id == goal_id,
        HouseholdGoal.household_id == household_id,
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return {"deleted": True}


# ── Helpers ──────────────────────────────────────────────────────────────


def _household_to_dict(household: Household) -> dict:
    return {
        "id": str(household.id),
        "name": household.name,
        "owner_id": str(household.owner_id),
        "created_at": household.created_at.isoformat(),
        "updated_at": household.updated_at.isoformat(),
        "members": [_member_to_dict(m) for m in household.members],
    }


def _member_to_dict(member: HouseholdMember) -> dict:
    return {
        "id": str(member.id),
        "household_id": str(member.household_id),
        "user_id": str(member.user_id) if member.user_id else None,
        "email": member.email,
        "role": member.role,
        "status": member.status,
        "invited_at": member.invited_at.isoformat(),
        "accepted_at": member.accepted_at.isoformat() if member.accepted_at else None,
    }


def _goal_to_dict(goal: HouseholdGoal) -> dict:
    return {
        "id": str(goal.id),
        "household_id": str(goal.household_id),
        "name": goal.name,
        "target_amount": goal.target_amount,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "goal_type": goal.goal_type,
        "currency": goal.currency,
        "emoji": goal.emoji,
        "created_at": goal.created_at.isoformat(),
    }
