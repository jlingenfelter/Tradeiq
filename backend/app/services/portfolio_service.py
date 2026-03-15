import uuid

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Account
from app.models.user import User
from app.core.exceptions import NotFoundError, ForbiddenError


def get_portfolio(db: Session, portfolio_id: uuid.UUID, user: User) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise NotFoundError("Portfolio not found")
    if portfolio.user_id != user.id:
        raise ForbiddenError()
    return portfolio


def list_portfolios(db: Session, user: User) -> list[Portfolio]:
    return db.query(Portfolio).filter(Portfolio.user_id == user.id).all()


def create_portfolio(db: Session, user: User, name: str, base_currency: str = "USD") -> Portfolio:
    portfolio = Portfolio(user_id=user.id, name=name, base_currency=base_currency)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    # Create default account
    account = Account(portfolio_id=portfolio.id, name="Default", source_type="manual")
    db.add(account)
    db.commit()
    return portfolio


def update_portfolio(db: Session, portfolio: Portfolio, name: str | None, base_currency: str | None) -> Portfolio:
    if name is not None:
        portfolio.name = name
    if base_currency is not None:
        portfolio.base_currency = base_currency
    db.commit()
    db.refresh(portfolio)
    return portfolio


def delete_portfolio(db: Session, portfolio: Portfolio) -> None:
    db.delete(portfolio)
    db.commit()


def get_or_create_default_account(db: Session, portfolio: Portfolio) -> Account:
    account = db.query(Account).filter(
        Account.portfolio_id == portfolio.id, Account.source_type == "manual"
    ).first()
    if not account:
        account = Account(portfolio_id=portfolio.id, name="Default", source_type="manual")
        db.add(account)
        db.commit()
        db.refresh(account)
    return account


def create_account(db: Session, portfolio: Portfolio, name: str, source_type: str) -> Account:
    account = Account(portfolio_id=portfolio.id, name=name, source_type=source_type)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
