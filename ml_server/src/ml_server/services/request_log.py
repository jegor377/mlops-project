# services/request_log.py
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.request_log import ApiRequestLog

logger = logging.getLogger(__name__)

# Keep at most this many rows per user — oldest are pruned after insert
MAX_LOGS_PER_USER = 100


async def record_request(
    db: AsyncSession,
    *,
    user_id: int,
    pat_id: int,
    method: str,
    path: str,
    status_code: int,
    latency_ms: int,
    ip: str | None,
) -> None:
    """
    Persist one API request log entry, then prune oldest rows so we never
    store more than MAX_LOGS_PER_USER rows per user.
    Called from a BackgroundTask — do NOT share the request-scoped session.
    Open a fresh session via the factory passed from the route instead.
    """
    entry = ApiRequestLog(
        user_id=user_id,
        pat_id=pat_id,
        method=method,
        path=path,
        status_code=status_code,
        latency_ms=latency_ms,
        ip=ip,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.flush()

    # Prune: delete all rows beyond the MAX_LOGS_PER_USER newest
    subq = (
        select(ApiRequestLog.id)
        .where(ApiRequestLog.user_id == user_id)
        .order_by(ApiRequestLog.created_at.desc())
        .offset(MAX_LOGS_PER_USER)
        .subquery()
    )
    await db.execute(
        delete(ApiRequestLog).where(ApiRequestLog.id.in_(select(subq.c.id)))
    )
    await db.commit()
