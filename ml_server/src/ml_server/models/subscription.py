from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, DateTime, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from src.ml_server.models.base import Base

if TYPE_CHECKING:
    from src.ml_server.models.user import User
    from src.ml_server.models.plan import Plan


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)

    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status", native_enum=True),
        server_default=text("'active'"),
        nullable=False,
    )

    # overrides for negotiated Custom-plan terms; NULL falls back to Plan defaults
    custom_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    custom_terms: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")
