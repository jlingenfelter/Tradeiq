import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.position import Position
from app.schemas.position import PositionCreate, PositionUpdate, PositionResponse
from app.services.portfolio_service import get_portfolio, get_or_create_default_account

router = APIRouter(tags=["positions"])


@router.get("/portfolios/{portfolio_id}/positions", response_model=list[PositionResponse])
def list_positions(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    positions = (
        db.query(Position)
        .join(Position.account)
        .filter(Position.account.has(portfolio_id=portfolio.id))
        .all()
    )
    return [PositionResponse(
        id=str(p.id), account_id=str(p.account_id), symbol=p.symbol,
        asset_name=p.asset_name, asset_type=p.asset_type, quantity=p.quantity,
        cost_basis_total=p.cost_basis_total, cost_basis_per_share=p.cost_basis_per_share,
        currency=p.currency, created_at=p.created_at,
    ) for p in positions]


@router.post("/portfolios/{portfolio_id}/positions", response_model=PositionResponse)
def create_position(
    portfolio_id: uuid.UUID,
    body: PositionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)

    if body.account_id:
        from app.models.portfolio import Account
        account = db.query(Account).filter(
            Account.id == uuid.UUID(body.account_id),
            Account.portfolio_id == portfolio.id,
        ).first()
        if not account:
            raise NotFoundError("Account not found")
    else:
        account = get_or_create_default_account(db, portfolio)

    position = Position(
        account_id=account.id,
        symbol=body.symbol.upper().strip(),
        asset_name=body.asset_name,
        asset_type=body.asset_type,
        quantity=body.quantity,
        cost_basis_total=body.cost_basis_total,
        cost_basis_per_share=body.cost_basis_per_share,
        currency=body.currency,
    )
    db.add(position)
    db.commit()
    db.refresh(position)

    return PositionResponse(
        id=str(position.id), account_id=str(position.account_id), symbol=position.symbol,
        asset_name=position.asset_name, asset_type=position.asset_type, quantity=position.quantity,
        cost_basis_total=position.cost_basis_total, cost_basis_per_share=position.cost_basis_per_share,
        currency=position.currency, created_at=position.created_at,
    )


@router.patch("/positions/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: uuid.UUID,
    body: PositionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise NotFoundError("Position not found")

    # Verify ownership through account -> portfolio -> user
    from app.models.portfolio import Account, Portfolio
    account = db.query(Account).filter(Account.id == position.account_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == account.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise NotFoundError("Position not found")

    if body.quantity is not None:
        position.quantity = body.quantity
    if body.cost_basis_total is not None:
        position.cost_basis_total = body.cost_basis_total
    if body.cost_basis_per_share is not None:
        position.cost_basis_per_share = body.cost_basis_per_share

    db.commit()
    db.refresh(position)

    return PositionResponse(
        id=str(position.id), account_id=str(position.account_id), symbol=position.symbol,
        asset_name=position.asset_name, asset_type=position.asset_type, quantity=position.quantity,
        cost_basis_total=position.cost_basis_total, cost_basis_per_share=position.cost_basis_per_share,
        currency=position.currency, created_at=position.created_at,
    )


@router.delete("/positions/{position_id}")
def delete_position(
    position_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise NotFoundError("Position not found")

    from app.models.portfolio import Account, Portfolio
    account = db.query(Account).filter(Account.id == position.account_id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.id == account.portfolio_id).first()
    if portfolio.user_id != current_user.id:
        raise NotFoundError("Position not found")

    db.delete(position)
    db.commit()
    return {"message": "Position deleted"}
