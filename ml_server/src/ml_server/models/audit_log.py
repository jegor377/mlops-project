# models/audit_log.py
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.ml_server.models.base import Base

if TYPE_CHECKING:
    from src.ml_server.models.user import User


class AuditCategory(str, enum.Enum):
    pat = "pat"
    auth = "auth"
    account = "account"


# Mapping: event string → category
EVENT_CATEGORY: dict[str, AuditCategory] = {
    "pat.created":                 AuditCategory.pat,
    "pat.revoked":                 AuditCategory.pat,
    "auth.login":                  AuditCategory.auth,
    "auth.login_failed":           AuditCategory.auth,
    "auth.logout":                 AuditCategory.auth,
    "auth.oauth_login":            AuditCategory.auth,
    "account.email_verified":      AuditCategory.account,
    "account.password_changed":    AuditCategory.account,
    "account.verification_resent": AuditCategory.account,
}


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[AuditCategory] = mapped_column(
        Enum(AuditCategory), nullable=False, index=True
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="audit_logs")
