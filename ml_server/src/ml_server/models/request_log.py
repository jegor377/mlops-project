# models/request_log.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.ml_server.models.base import Base

if TYPE_CHECKING:
    from src.ml_server.models.user import User
    from src.ml_server.models.pat import PersonalAccessToken


class ApiRequestLog(Base):
    __tablename__ = "api_request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pat_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("personal_access_tokens.id", ondelete="SET NULL"), nullable=True
    )
    method: Mapped[str] = mapped_column(String(8), nullable=False)
    path: Mapped[str] = mapped_column(String(256), nullable=False)
    status_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="request_logs")
    pat: Mapped["PersonalAccessToken"] = relationship("PersonalAccessToken")
