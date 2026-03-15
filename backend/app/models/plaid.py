import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Boolean, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlaidItem(Base):
    """Represents a Plaid Link connection to a financial institution."""
    __tablename__ = "plaid_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    plaid_item_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    plaid_access_token: Mapped[str] = mapped_column(Text, nullable=False)  # encrypted at rest
    institution_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # status: active, error, needs_reauth
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    consent_expiration: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="plaid_items")
    accounts = relationship("PlaidAccount", back_populates="plaid_item", cascade="all, delete-orphan")


class PlaidAccount(Base):
    """Represents a single bank/investment account from a Plaid Item."""
    __tablename__ = "plaid_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plaid_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plaid_items.id"), nullable=False, index=True)
    plaid_account_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    container_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wealth_containers.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    official_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # account_type: depository, investment, credit, loan
    account_subtype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    available_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    plaid_item = relationship("PlaidItem", back_populates="accounts")
    container = relationship("WealthContainer")
