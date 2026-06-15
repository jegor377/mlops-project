# routes/requests.py
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from redis.asyncio import Redis
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import cast, Date

from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.current_user import get_current_user
from src.ml_server.models.request_log import ApiRequestLog
from src.ml_server.models.user import User
from src.ml_server.schemas.requests import (
    RequestLogResponse, RequestLogPage, RequestStatsResponse
)


router = APIRouter()


# ── Helper ────────────────────────────────────────────────────────────────────

def _status_condition(status: str):
    """Translate filter string to SQLAlchemy condition or None."""
    if status == "2xx":
        return and_(ApiRequestLog.status_code >= 200, ApiRequestLog.status_code < 300)
    if status == "4xx":
        return and_(ApiRequestLog.status_code >= 400, ApiRequestLog.status_code < 500)
    if status == "5xx":
        return and_(ApiRequestLog.status_code >= 500, ApiRequestLog.status_code < 600)
    return None  # "all"


# ── GET /api/requests ─────────────────────────────────────────────────────────

@router.get("/api/requests", response_model=RequestLogPage)
async def list_requests(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str = Query("all", pattern="^(all|2xx|4xx|5xx)$"),
) -> RequestLogPage:
    base = select(ApiRequestLog).where(ApiRequestLog.user_id == current_user.id)

    cond = _status_condition(status)
    if cond is not None:
        base = base.where(cond)

    total_result = await session.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = total_result.scalar_one()

    result = await session.execute(
        base.order_by(ApiRequestLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = result.scalars().all()

    return RequestLogPage(
        items=[
            RequestLogResponse(
                id=r.id,
                method=r.method,
                path=r.path,
                status_code=r.status_code,
                latency_ms=r.latency_ms,
                ip=r.ip,
                created_at=r.created_at.isoformat(),
            )
            for r in items
        ],
        total=total,
        page=page,
        size=size,
    )


# ── GET /api/requests/stats ───────────────────────────────────────────────────

@router.get("/api/requests/stats", response_model=RequestStatsResponse)
async def get_request_stats(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    daily_limit: int = Query(1000, ge=1, le=2000),
) -> RequestStatsResponse:

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    twenty_days_ago = today_start - timedelta(days=19)

    uid = current_user.id
    redis: Redis = request.app.state.redis

    # Requests today — z Redisa (ten sam klucz co rate limiter)
    raw = await redis.get(f"rl:{uid}")
    requests_today = int(raw) if raw else 0

    # Requests this month — z bazy (Redis nie trzyma historii)
    month_result = await session.execute(
        select(func.count()).where(
            ApiRequestLog.user_id == uid,
            ApiRequestLog.created_at >= month_start,
        )
    )
    requests_this_month = month_result.scalar_one()

    # Avg latency + error rate — ostatnie 100 wpisów z bazy
    last100_result = await session.execute(
        select(ApiRequestLog.latency_ms, ApiRequestLog.status_code)
        .where(ApiRequestLog.user_id == uid)
        .order_by(ApiRequestLog.created_at.desc())
        .limit(100)
    )
    last100 = last100_result.all()

    avg_latency_ms: int | None = None
    error_rate: float | None = None
    if last100:
        avg_latency_ms = round(sum(r.latency_ms for r in last100) / len(last100))
        errors = sum(1 for r in last100 if r.status_code >= 400)
        error_rate = round(errors / len(last100), 4)

    # Spark — GROUP BY day z bazy (Redis nie ma historii dni)
    spark_result = await session.execute(
        select(
            cast(ApiRequestLog.created_at, Date).label("day"),
            func.count().label("cnt"),
        )
        .where(
            ApiRequestLog.user_id == uid,
            ApiRequestLog.created_at >= twenty_days_ago,
        )
        .group_by("day")
    )
    counts_by_day = {row.day: row.cnt for row in spark_result.all()}

    spark: list[int] = []
    for i in range(20):
        day = (twenty_days_ago + timedelta(days=i)).date()
        spark.append(counts_by_day.get(day, 0))

    # Overwrite the last Spark bar with the value from Redis
    # the database may not have all the requests from today yet (BackgroundTask lag)

    spark[19] = requests_today

    return RequestStatsResponse(
        requests_today=requests_today,
        daily_limit=daily_limit,
        requests_this_month=requests_this_month,
        avg_latency_ms=avg_latency_ms,
        error_rate=error_rate,
        spark=spark,
    )
