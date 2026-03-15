import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    AccountCreate, AccountResponse,
)
from app.services.portfolio_service import (
    list_portfolios, create_portfolio, get_portfolio,
    update_portfolio, delete_portfolio, create_account,
)
from app.services.audit_service import log_event
from app.core.tier_gate import get_user_tier

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=list[PortfolioResponse])
def list_user_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolios = list_portfolios(db, current_user)
    return [PortfolioResponse(id=str(p.id), name=p.name, base_currency=p.base_currency,
                               created_at=p.created_at, updated_at=p.updated_at) for p in portfolios]


@router.post("", response_model=PortfolioResponse)
def create_new_portfolio(
    body: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Free tier: max 1 portfolio
    tier = get_user_tier(db, current_user.id)
    if tier == "free":
        existing = list_portfolios(db, current_user)
        if len(existing) >= 1:
            from app.core.exceptions import ForbiddenError
            raise ForbiddenError("Free plan is limited to 1 portfolio. Upgrade to Pro for unlimited.")
    portfolio = create_portfolio(db, current_user, body.name, body.base_currency)
    log_event(db, current_user.id, "portfolio_created", {"portfolio_id": str(portfolio.id)})
    return PortfolioResponse(id=str(portfolio.id), name=portfolio.name, base_currency=portfolio.base_currency,
                              created_at=portfolio.created_at, updated_at=portfolio.updated_at)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio_detail(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    return PortfolioResponse(id=str(portfolio.id), name=portfolio.name, base_currency=portfolio.base_currency,
                              created_at=portfolio.created_at, updated_at=portfolio.updated_at)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio_detail(
    portfolio_id: uuid.UUID,
    body: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    portfolio = update_portfolio(db, portfolio, body.name, body.base_currency)
    return PortfolioResponse(id=str(portfolio.id), name=portfolio.name, base_currency=portfolio.base_currency,
                              created_at=portfolio.created_at, updated_at=portfolio.updated_at)


@router.delete("/{portfolio_id}")
def delete_portfolio_endpoint(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    log_event(db, current_user.id, "portfolio_deleted", {"portfolio_id": str(portfolio.id)})
    delete_portfolio(db, portfolio)
    return {"message": "Portfolio deleted"}


@router.get("/{portfolio_id}/accounts", response_model=list[AccountResponse])
def list_accounts(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    return [AccountResponse(id=str(a.id), portfolio_id=str(a.portfolio_id), name=a.name,
                             source_type=a.source_type, created_at=a.created_at) for a in portfolio.accounts]


@router.post("/{portfolio_id}/accounts", response_model=AccountResponse)
def create_new_account(
    portfolio_id: uuid.UUID,
    body: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    account = create_account(db, portfolio, body.name, body.source_type)
    return AccountResponse(id=str(account.id), portfolio_id=str(account.portfolio_id), name=account.name,
                            source_type=account.source_type, created_at=account.created_at)
