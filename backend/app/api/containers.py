import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.wealth import WealthContainer
from app.schemas.wealth import ContainerCreate, ContainerUpdate, ContainerResponse

router = APIRouter(prefix="/containers", tags=["containers"])


@router.get("", response_model=list[ContainerResponse])
def list_containers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    containers = db.query(WealthContainer).filter(
        WealthContainer.user_id == current_user.id
    ).order_by(WealthContainer.created_at).all()
    return [_to_response(c) for c in containers]


@router.post("", response_model=ContainerResponse)
def create_container(
    body: ContainerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    container = WealthContainer(
        user_id=current_user.id,
        name=body.name,
        container_type=body.container_type,
        institution_name=body.institution_name,
        currency=body.currency,
    )
    db.add(container)
    db.commit()
    db.refresh(container)
    return _to_response(container)


@router.patch("/{container_id}", response_model=ContainerResponse)
def update_container(
    container_id: uuid.UUID,
    body: ContainerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    container = _get_container(db, container_id, current_user.id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(container, field, value)
    db.commit()
    db.refresh(container)
    return _to_response(container)


@router.delete("/{container_id}")
def delete_container(
    container_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    container = _get_container(db, container_id, current_user.id)
    db.delete(container)
    db.commit()
    return {"message": "Container deleted"}


def _get_container(db: Session, container_id: uuid.UUID, user_id: uuid.UUID) -> WealthContainer:
    container = db.query(WealthContainer).filter(
        WealthContainer.id == container_id,
        WealthContainer.user_id == user_id,
    ).first()
    if not container:
        raise NotFoundError("Container not found")
    return container


def _to_response(c: WealthContainer) -> ContainerResponse:
    return ContainerResponse(
        id=str(c.id), name=c.name, container_type=c.container_type,
        institution_name=c.institution_name, currency=c.currency,
        created_at=c.created_at, updated_at=c.updated_at,
    )
