import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Boolean, Text, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WealthContainer(Base):
    """Represents an account, wallet, property bucket, business bucket, or manual grouping."""
    __tablename__ = "wealth_containers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    container_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # container_type: brokerage, pension, bank, crypto_wallet, property, business, liability_account, collectibles, manual
    institution_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="containers")
    assets = relationship("Asset", back_populates="container", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="container", cascade="all, delete-orphan")


class Asset(Base):
    """Tracks any kind of asset across all wealth categories."""
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    container_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wealth_containers.id"), nullable=True, index=True)
    asset_class: Mapped[str] = mapped_column(String(50), nullable=False)
    # asset_class: cash, stock, etf, mutual_fund, bond, pension, crypto, property, business_equity,
    #   gold, watch, collectible, private_loan_receivable, other
    asset_subclass: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    cost_basis: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    ownership_pct: Mapped[float | None] = mapped_column(Float, nullable=True, default=100.0)
    liquidity_category: Mapped[str] = mapped_column(String(20), nullable=False, default="liquid")
    # liquidity_category: highly_liquid, liquid, semi_liquid, illiquid
    valuation_source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    # valuation_source: market, manual, imported, estimated
    valuation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # metadata_json can store: address, interest_rate, monthly_rent, annual_expenses, valuation_method, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="assets")
    container = relationship("WealthContainer", back_populates="assets")


class Liability(Base):
    """Tracks debts and liabilities."""
    __tablename__ = "liabilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    container_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wealth_containers.id"), nullable=True, index=True)
    liability_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # liability_type: mortgage, loan, credit_card, tax, margin, business_debt, other
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_balance: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    interest_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    monthly_payment: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    linked_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="liabilities")
    container = relationship("WealthContainer", back_populates="liabilities")
    linked_asset = relationship("Asset", foreign_keys=[linked_asset_id])


class WealthSnapshot(Base):
    """Stores the full-user wealth snapshot over time."""
    __tablename__ = "wealth_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    total_assets: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_liabilities: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    net_worth: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    liquid_assets: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    illiquid_assets: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    liquid_net_worth: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    cash_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    investment_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    property_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    crypto_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    business_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    pension_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    other_asset_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    debt_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="wealth_snapshots")
    allocation_snapshot = relationship("AllocationSnapshot", back_populates="wealth_snapshot", uselist=False)


class AllocationSnapshot(Base):
    """Stores allocation breakdown at a point in time."""
    __tablename__ = "allocation_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    wealth_snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wealth_snapshots.id"), nullable=False)
    asset_class_allocations_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    liquidity_allocations_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    geography_allocations_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sector_allocations_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    top_concentrations_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    health_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    health_score_breakdown_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    warnings_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    wealth_snapshot = relationship("WealthSnapshot", back_populates="allocation_snapshot")


class ImportJob(Base):
    """Tracks import operations."""
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    import_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # status: pending, processing, completed, failed
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AISummary(Base):
    """Stores AI-generated summaries."""
    __tablename__ = "ai_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    summary_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # summary_type: wealth_overview, portfolio, property, crypto, etc.
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    structured_input_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
