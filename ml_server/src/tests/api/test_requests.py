"""Tests for API Request Log and Stats endpoints."""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from src.tests.conftest import make_classic_user, make_session


# ── Helpers ──────────────────────────────────────────────────────────────────

LIST_URL = "/api/requests"
STATS_URL = "/api/requests/stats"


async def make_request_log(session, user_id: int, status_code: int = 200, latency_ms: int = 150, created_at=None):
    """Helper to persist ApiRequestLog records for testing."""
    from src.ml_server.models.request_log import ApiRequestLog

    log = ApiRequestLog(
        user_id=user_id,
        method="POST",
        path="/api/v1/predict",
        status_code=status_code,
        latency_ms=latency_ms,
        ip="127.0.0.1",
        created_at=created_at or datetime.now(timezone.utc)
    )
    session.add(log)
    await session.commit()
    return log


# ── GET /api/requests ─────────────────────────────────────────────────────────


async def test_list_requests_returns_only_own_logs(client, db_session):
    user1 = await make_classic_user(db_session, "user1@example.com")
    user2 = await make_classic_user(db_session, "user2@example.com")
    us1 = await make_session(db_session, user1)

    await make_request_log(db_session, user_id=user1.id, status_code=200)
    await make_request_log(db_session, user_id=user2.id, status_code=500)  # should NOT appear

    client.cookies.set("session", us1.token)
    resp = await client.get(LIST_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status_code"] == 200


async def test_list_requests_pagination(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    # Create 25 logs
    for _ in range(25):
        await make_request_log(db_session, user_id=user.id)

    resp = await client.get(f"{LIST_URL}?page=2&size=10")

    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["size"] == 10
    assert data["total"] == 25
    assert len(data["items"]) == 10


async def test_list_requests_invalid_params_returns_422(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    # Page/size limits validation
    resp = await client.get(f"{LIST_URL}?page=0")
    assert resp.status_code == 422

    resp = await client.get(f"{LIST_URL}?size=101")
    assert resp.status_code == 422


async def test_list_requests_status_filter_2xx(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    await make_request_log(db_session, user_id=user.id, status_code=201)
    await make_request_log(db_session, user_id=user.id, status_code=404)

    resp = await client.get(f"{LIST_URL}?status=2xx")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status_code"] == 201


async def test_list_requests_status_filter_4xx_and_5xx(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    await make_request_log(db_session, user_id=user.id, status_code=400)
    await make_request_log(db_session, user_id=user.id, status_code=503)

    resp = await client.get(f"{LIST_URL}?status=4xx")
    assert resp.json()["total"] == 1

    resp = await client.get(f"{LIST_URL}?status=5xx")
    assert resp.json()["total"] == 1


async def test_list_requests_invalid_status_pattern_returns_422(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get(f"{LIST_URL}?status=3xx")
    assert resp.status_code == 422


async def test_list_requests_unauthenticated_returns_401(client):
    resp = await client.get(LIST_URL)
    assert resp.status_code == 401


# ── GET /api/requests/stats ───────────────────────────────────────────────────


async def test_get_request_stats_success(client, db_session, app):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    # Mock Redis rate-limiter response
    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"42"
    app.state.redis = mock_redis

    now = datetime.now(timezone.utc)

    # Create logs to test avg latency (150 + 250 / 2 = 200) and error rate (1/2 = 0.5)
    await make_request_log(db_session, user_id=user.id, status_code=200, latency_ms=150, created_at=now)
    await make_request_log(db_session, user_id=user.id, status_code=500, latency_ms=250, created_at=now)

    resp = await client.get(f"{STATS_URL}?daily_limit=2000")

    assert resp.status_code == 200
    data = resp.json()
    assert data["requests_today"] == 42
    assert data["daily_limit"] == 2000
    assert data["requests_this_month"] == 2
    assert data["avg_latency_ms"] == 200
    assert data["error_rate"] == 0.5000
    assert len(data["spark"]) == 20
    assert data["spark"][-1] == 42  # Overwritten by Redis value
    mock_redis.get.assert_awaited_once_with(f"rl:{user.id}")


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
    assert data["spark"][-1] == 0


async def test_get_request_stats_empty_db_returns_none_metrics(client, db_session, app):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"0"
    app.state.redis = mock_redis

    resp = await client.get(STATS_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert data["avg_latency_ms"] is None
    assert data["error_rate"] is None
    assert all(val == 0 for val in data["spark"])


async def test_get_request_stats_spark_historical_aggregation(client, db_session, app):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"5"
    app.state.redis = mock_redis

    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)

    # Historical logs
    await make_request_log(db_session, user_id=user.id, created_at=two_days_ago)
    await make_request_log(db_session, user_id=user.id, created_at=yesterday)
    await make_request_log(db_session, user_id=user.id, created_at=yesterday)

    resp = await client.get(STATS_URL)

    assert resp.status_code == 200
    spark = resp.json()["spark"]
    assert spark[-1] == 5  # Today (Redis overwrite)
    assert spark[-2] == 2  # Yesterday
    assert spark[-3] == 1  # 2 days ago


async def test_get_request_stats_unauthenticated_returns_401(client):
    resp = await client.get(STATS_URL)
    assert resp.status_code == 401
