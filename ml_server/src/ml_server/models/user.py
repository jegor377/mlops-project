from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, func, text

from src.ml_server.models.base import Base

# make linter be quiet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ml_server.models.user_auth_method import UserAuthMethod
    from src.ml_server.models.audit_log import AuditLog


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    auth_methods: Mapped[list["UserAuthMethod"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
