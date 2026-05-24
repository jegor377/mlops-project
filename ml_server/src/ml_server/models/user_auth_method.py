from enum import StrEnum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, ForeignKey, UniqueConstraint, func, DateTime, String

from src.ml_server.models.base import Base


class AuthProvider(StrEnum):
    CLASSIC = "classic"
    GOOGLE = "google"
    GITHUB = "github"


class UserAuthMethod(Base):
    __tablename__ = "user_auth_methods"

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_provider_user_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider),
        nullable=False,
    )

    # Google sub, GitHub id, etc.
    provider_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # only used for classic auth
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="auth_methods",
    )
