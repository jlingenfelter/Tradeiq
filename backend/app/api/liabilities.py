import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.wealth import Liability
from app.schemas.wealth import LiabilityCreate, LiabilityUpdate, LiabilityResponse

router = APIRouter(prefix="/liabilities", tags=["liabilities"])


@router.get("", response_model=list[LiabilityResponse])
def list_liabilities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(Liability).filter(
        Liability.user_id == current_user.id
    ).order_by(Liability.current_balance.desc()).all()
    return [_to_response(l) for l in items]


@router.post("", response_model=LiabilityResponse)
def create_liability(
    body: LiabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    liability = Liability(
        user_id=current_user.id,
        container_id=uuid.UUID(body.container_id) if body.container_id else None,
        liability_type=body.liability_type,
        name=body.name,
        current_balance=body.current_balance,
        currency=body.currency,
        interest_rate=body.interest_rate,
        monthly_payment=body.monthly_payment,
        due_date=body.due_date,
        linked_asset_id=uuid.UUID(body.linked_asset_id) if body.linked_asset_id else None,
        notes=body.notes,
    )
    db.add(liability)
    db.commit()
    db.refresh(liability)
    return _to_response(liability)


@router.patch("/{liability_id}", response_model=LiabilityResponse)
def update_liability(
    liability_id: uuid.UUID,
    body: LiabilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    liability = _get_liability(db, liability_id, current_user.id)
    data = body.model_dump(exclude_unset=True)
    if "container_id" in data and data["container_id"]:
        data["container_id"] = uuid.UUID(data["container_id"])
    if "linked_asset_id" in data and data["linked_asset_id"]:
        data["linked_asset_id"] = uuid.UUID(data["linked_asset_id"])
    for field, value in data.items():
        setattr(liability, field, value)
    db.commit()
    db.refresh(liability)
    return _to_response(liability)


@router.delete("/{liability_id}")
def delete_liability(
    liability_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    liability = _get_liability(db, liability_id, current_user.id)
    db.delete(liability)
    db.commit()
    return {"message": "Liability deleted"}


def _get_liability(db: Session, liability_id: uuid.UUID, user_id: uuid.UUID) -> Liability:
    liability = db.query(Liability).filter(
        Liability.id == liability_id, Liability.user_id == user_id,
    ).first()
    if not liability:
        raise NotFoundError("Liability not found")
    return liability


def _to_response(l: Liability) -> LiabilityResponse:
    return LiabilityResponse(
        id=str(l.id),
        container_id=str(l.container_id) if l.container_id else None,
        liability_type=l.liability_type,
        name=l.name,
        current_balance=l.current_balance,
        currency=l.currency,
        interest_rate=l.interest_rate,
        monthly_payment=l.monthly_payment,
        due_date=l.due_date,
        linked_asset_id=str(l.linked_asset_id) if l.linked_asset_id else None,
        notes=l.notes,
        created_at=l.created_at,
        updated_at=l.updated_at,
    )
