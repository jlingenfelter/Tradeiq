import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.wealth import Asset
from app.schemas.wealth import AssetCreate, AssetUpdate, AssetResponse

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[AssetResponse])
def list_assets(
    asset_class: str | None = Query(None),
    container_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Asset).filter(Asset.user_id == current_user.id)
    if asset_class:
        q = q.filter(Asset.asset_class == asset_class)
    if container_id:
        q = q.filter(Asset.container_id == uuid.UUID(container_id))
    assets = q.order_by(Asset.current_value.desc()).all()
    return [_to_response(a) for a in assets]


@router.post("", response_model=AssetResponse)
def create_asset(
    body: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = Asset(
        user_id=current_user.id,
        container_id=uuid.UUID(body.container_id) if body.container_id else None,
        asset_class=body.asset_class,
        asset_subclass=body.asset_subclass,
        name=body.name,
        symbol=body.symbol,
        quantity=body.quantity,
        unit_value=body.unit_value,
        current_value=body.current_value,
        cost_basis=body.cost_basis,
        currency=body.currency,
        ownership_pct=body.ownership_pct,
        liquidity_category=body.liquidity_category,
        valuation_source=body.valuation_source,
        country=body.country,
        sector=body.sector,
        notes=body.notes,
        metadata_json=body.metadata_json,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _to_response(asset)


@router.patch("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: uuid.UUID,
    body: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = _get_asset(db, asset_id, current_user.id)
    data = body.model_dump(exclude_unset=True)
    if "container_id" in data and data["container_id"]:
        data["container_id"] = uuid.UUID(data["container_id"])
    for field, value in data.items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return _to_response(asset)


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = _get_asset(db, asset_id, current_user.id)
    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted"}


def _get_asset(db: Session, asset_id: uuid.UUID, user_id: uuid.UUID) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.user_id == user_id).first()
    if not asset:
        raise NotFoundError("Asset not found")
    return asset


def _to_response(a: Asset) -> AssetResponse:
    return AssetResponse(
        id=str(a.id),
        container_id=str(a.container_id) if a.container_id else None,
        asset_class=a.asset_class,
        asset_subclass=a.asset_subclass,
        name=a.name,
        symbol=a.symbol,
        quantity=a.quantity,
        unit_value=a.unit_value,
        current_value=a.current_value,
        cost_basis=a.cost_basis,
        currency=a.currency,
        ownership_pct=a.ownership_pct,
        liquidity_category=a.liquidity_category,
        valuation_source=a.valuation_source,
        valuation_date=a.valuation_date,
        country=a.country,
        sector=a.sector,
        notes=a.notes,
        metadata_json=a.metadata_json,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )
