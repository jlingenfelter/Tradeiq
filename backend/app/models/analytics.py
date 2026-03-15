import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    cash_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio = relationship("Portfolio", back_populates="portfolio_snapshots")
    analytics_snapshot = relationship("AnalyticsSnapshot", back_populates="portfolio_snapshot", uselist=False)


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    portfolio_snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolio_snapshots.id"), nullable=False)
    health_score: Mapped[float] = mapped_column(Float, nullable=False)
    top_holding_weight: Mapped[float] = mapped_column(Float, nullable=False)
    top_3_weight: Mapped[float] = mapped_column(Float, nullable=False)
    top_5_weight: Mapped[float] = mapped_column(Float, nullable=False)
    sector_concentration_score: Mapped[float] = mapped_column(Float, nullable=False)
    country_concentration_score: Mapped[float] = mapped_column(Float, nullable=False)
    benchmark_tracking_diff: Mapped[float | None] = mapped_column(Float, nullable=True)
    volatility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    diversification_score: Mapped[float] = mapped_column(Float, nullable=False)
    event_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    analytics_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")

    # Store detailed breakdown as JSON for flexibility
    sector_exposure: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    country_exposure: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    stress_tests: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    health_score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    holdings_detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio = relationship("Portfolio", back_populates="analytics_snapshots")
    portfolio_snapshot = relationship("PortfolioSnapshot", back_populates="analytics_snapshot")
    warnings = relationship("Warning", back_populates="analytics_snapshot")
