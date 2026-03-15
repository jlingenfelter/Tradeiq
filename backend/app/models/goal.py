import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Boolean, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WealthGoal(Base):
    """Net worth or savings goal with target amount and deadline."""
    __tablename__ = "wealth_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    goal_type: Mapped[str] = mapped_column(String(50), nullable=False, default="net_worth")
    # goal_type: net_worth, savings, debt_payoff, investment, emergency_fund
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    emoji: Mapped[str] = mapped_column(String(10), nullable=False, default="🎯")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="goals")
