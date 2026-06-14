# dependencies/rate_limit.py
from __future__ import annotations

from datetime import timezone, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis

from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.dependencies.pat_token import get_pat
from src.ml_server.dependencies.settings import get_settings
from src.ml_server.conf.settings import Settings


def _redis(request: Request) -> Redis:
    return request.app.state.redis


def _next_midnight() -> datetime:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return tomorrow


async def check_rate_limit(
    pat: Annotated[PersonalAccessToken, Depends(get_pat(scopes=["inference:basic"]))],
    settings: Annotated[Settings, Depends(get_settings)],
    request: Request,
) -> PersonalAccessToken:
    """
    Daily sliding window counter in Redis, keyed per user.
    Key: rl:{user_id} — expires at next UTC midnight.
    Attaches rl_count / rl_remaining / rl_limit to request.state
    so the route can forward them as response headers.
    """
    redis: Redis = _redis(request)
    key = f"rl:{pat.user_id}"
    limit: int = settings.daily_request_limit  # add to Settings, e.g. 1000

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expireat(key, _next_midnight())
    count, _ = await pipe.execute()

    remaining = max(0, limit - count)
    request.state.rl_count = count
    request.state.rl_remaining = remaining
    request.state.rl_limit = limit

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail="Daily request limit exceeded. Resets at midnight UTC.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(_next_midnight().timestamp())),
                "Retry-After": "86400",
            },
        )

    return pat
