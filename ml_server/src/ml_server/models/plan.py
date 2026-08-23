from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, DateTime, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from src.ml_server.models.base import Base

if TYPE_CHECKING:
    from src.ml_server.models.subscription import Subscription


class PlanTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    CUSTOM = "custom"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    tier: Mapped[PlanTier] = mapped_column(
        SAEnum(PlanTier, name="plan_tier", native_enum=True),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)

    # cents; NULL = "negotiated" (Custom plan)
    price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # NULL = unlimited
    requests_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    api_key_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    history_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    priority_support: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    webhook_notifications: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    dedicated_support: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    custom_sla: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    on_prem: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")
