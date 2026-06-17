"""Tests for API Request Log and Stats endpoints."""
from unittest.mock import AsyncMock

from src.tests.conftest import make_classic_user, make_session


# ── Helpers ──────────────────────────────────────────────────────────────────

STATS_URL = "/api/requests/stats"


def redis_mock(user_id, rt, rtm, ls, lc):
    mock_redis = AsyncMock()
    mock_database = {
        f"rt:{user_id}": str(rt).encode('ascii'),
        f"rtm:{user_id}": str(rtm).encode('ascii'),
        f"ls:{user_id}": str(ls).encode('ascii'),
        f"lc:{user_id}": str(lc).encode('ascii'),
    }

    async def async_get(key, *args, **kwargs):
        return mock_database.get(key, None)

    mock_redis.get.side_effect = async_get
    return mock_redis


# ── GET /api/requests/stats ───────────────────────────────────────────────────


async def test_get_request_stats_success(client, db_session, app, test_settings):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    # Mock Redis response
    mock_redis = redis_mock(
        user_id=user.id,
        rt=42,
        rtm=120,
        ls=450,
        lc=10,
    )
    app.state.redis = mock_redis

    resp = await client.get(STATS_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert data["requests_today"] == 42
    assert data["daily_limit"] == test_settings.daily_request_limit
    assert data["requests_this_month"] == 120
    assert data["avg_latency_ms"] == 45
    mock_redis.get.assert_any_call(f"rt:{user.id}")
    mock_redis.get.assert_any_call(f"rtm:{user.id}")
    mock_redis.get.assert_any_call(f"ls:{user.id}")
    mock_redis.get.assert_any_call(f"lc:{user.id}")


async def test_get_request_stats_redis_empty_defaults_to_zero(client, db_session, app):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Redis key missing
    app.state.redis = mock_redis

    resp = await client.get(STATS_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert data["requests_today"] == 0


async def test_get_request_stats_empty_db_returns_none_metrics(client, db_session, app):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    app.state.redis = redis_mock(
        user_id=user.id,
        rt=0,
        rtm=0,
        ls=0,
        lc=0,
    )

    resp = await client.get(STATS_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert data["avg_latency_ms"] is None


async def test_get_request_stats_unauthenticated_returns_401(client):
    resp = await client.get(STATS_URL)
    assert resp.status_code == 401
