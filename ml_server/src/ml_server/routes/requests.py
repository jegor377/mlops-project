# routes/requests.py
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.current_user import get_current_user
from src.ml_server.dependencies.settings import get_settings
from src.ml_server.models.user import User
from src.ml_server.schemas.requests import RequestStatsResponse
from src.ml_server.conf.settings import Settings


router = APIRouter()


@router.get("/api/requests/stats", response_model=RequestStatsResponse)
async def get_request_stats(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RequestStatsResponse:
    uid = current_user.id
    redis: Redis = request.app.state.redis

    raw_rt = await redis.get(f"rt:{uid}")
    requests_today = int(raw_rt) if raw_rt else 0

    raw_rtm = await redis.get(f"rtm:{uid}")
    requests_this_month = int(raw_rtm) if raw_rtm else 0

    raw_ls = await redis.get(f"ls:{uid}")
    latency_sum = int(raw_ls) if raw_ls else 0
    raw_lc = await redis.get(f"lc:{uid}")
    latency_count = int(raw_lc) if raw_lc else 0

    avg_latency_ms: int | None = int(latency_sum / latency_count) if latency_count != 0 else None

    daily_limit: int = settings.daily_request_limit

    return RequestStatsResponse(
        requests_today=requests_today,
        daily_limit=daily_limit,
        requests_this_month=requests_this_month,
        avg_latency_ms=avg_latency_ms,
        latency_count=latency_count,
    )
