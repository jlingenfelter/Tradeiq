import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    threshold_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="in_app")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alert_subscriptions")
