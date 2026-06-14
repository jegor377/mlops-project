# services/audit_log.py
"""
Helper to write audit log entries.  Call from route handlers — never from models.

Usage:
    from src.ml_server.services.audit_log import log_event

    await log_event(
        db,
        user_id=user.id,
        event="pat.created",
        request=request,
        metadata={"token_name": pat.name},
    )
"""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.audit_log import AuditLog, EventCategory, EVENT_CATEGORY


async def log_event(
    db: AsyncSession,
    *,
    user_id: int,
    event: EventCategory,
    request: Request | None = None,
    metadata: dict[str, str] | None = None,
) -> None:
    """Persist one audit log entry.  Does NOT commit — caller owns the transaction."""
    category = EVENT_CATEGORY.get(event)
    if category is None:
        raise ValueError(f"Unknown audit event: {event!r}")

    ip: str | None = None
    ua: str | None = None
    if request is not None:
        # Respect X-Forwarded-For when behind a proxy/gateway
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None
        ua = request.headers.get("User-Agent")
        if ua and len(ua) > 512:
            ua = ua[:509] + "…"

    entry = AuditLog(
        user_id=user_id,
        event=event,
        category=category,
        ip=ip,
        user_agent=ua,
        extra_metadata=metadata,
    )
    db.add(entry)
    # flush so the entry gets an id before any subsequent operations in same tx
    await db.flush()
