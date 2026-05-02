from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.ml_server.models.base import Base


class PersonalAccessToken(Base):
    __tablename__ = "personal_access_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Store only hash — never the raw token
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    # First 8 chars of raw token for display (e.g. "vlt_K9mX")
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    # Comma-separated scopes: "read:events,write:events"
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
