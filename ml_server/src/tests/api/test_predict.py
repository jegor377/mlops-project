from src.tests.conftest import make_classic_user, make_pat


async def test_ping(client):
    response = await client.get("/api/ping")
    assert response.status_code == 200


async def test_predict_dummy(client, db_session):
    user = await make_classic_user(db_session)
    _, raw_token = await make_pat(db_session, user, scopes=["inference:basic"])
    response = await client.post(
        "/api/predict",
        json={"text": "anything"},
        headers={"Authorization": f"Bearer {raw_token}"}
    )
    assert response.status_code == 200
    assert "prediction" in response.json()


async def test_predict_missing_field(client, db_session):
    user = await make_classic_user(db_session)
    _, raw_token = await make_pat(db_session, user, scopes=["inference:basic"])
    response = await client.post(
        "/api/predict",
        json={},
        headers={"Authorization": f"Bearer {raw_token}"}
    )
    assert response.status_code == 422


async def test_predict_dummy_unauthorized(client, db_session):
    response = await client.post(
        "/api/predict",
        json={"text": "anything"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


async def test_predict_dummy_insufficient_scopes(client, db_session):
    user = await make_classic_user(db_session)
    _, raw_token = await make_pat(db_session, user, scopes=["nonexistent:scope"])
    response = await client.post(
        "/api/predict",
        json={"text": "anything"},
        headers={"Authorization": f"Bearer {raw_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient scopes"


async def test_predict_returns_ratelimit_headers(client, db_session, test_settings):
    user = await make_classic_user(db_session)
    _, raw_token = await make_pat(db_session, user, scopes=["inference:basic"])

    resp = await client.post(
        "/api/predict",
        json={"text": "anything"},
        headers={"Authorization": f"Bearer {raw_token}"},
    )

    assert resp.status_code == 200
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers
    assert int(resp.headers["X-RateLimit-Limit"]) == test_settings.daily_request_limit
    assert int(resp.headers["X-RateLimit-Remaining"]) == test_settings.daily_request_limit - 1


async def test_predict_ratelimit_decrements_on_each_request(client, db_session):
    user = await make_classic_user(db_session)
    _, raw_token = await make_pat(db_session, user, scopes=["inference:basic"])
    headers = {"Authorization": f"Bearer {raw_token}"}

    for i in range(3):
        resp = await client.post("/api/predict", json={"text": "x"}, headers=headers)
        assert resp.status_code == 200

    remaining = int(resp.headers["X-RateLimit-Remaining"])
    limit = int(resp.headers["X-RateLimit-Limit"])
    assert remaining == limit - 3


async def test_predict_returns_429_when_limit_exceeded(client, db_session, app, test_settings):
    user = await make_classic_user(db_session)
    _, raw_token = await make_pat(db_session, user, scopes=["inference:basic"])

    await app.state.redis.set(f"rl:{user.id}", test_settings.daily_request_limit)

    resp = await client.post(
        "/api/predict",
        json={"text": "anything"},
        headers={"Authorization": f"Bearer {raw_token}"},
    )

    assert resp.status_code == 429
    assert "X-RateLimit-Remaining" in resp.headers
    assert resp.headers["X-RateLimit-Remaining"] == "0"
    assert "Retry-After" in resp.headers


async def test_predict_ratelimit_is_per_user(client, db_session, app, test_settings):
    """Limit user1 nie wpływa na user2."""
    user1 = await make_classic_user(db_session, "u1@example.com")
    user2 = await make_classic_user(db_session, "u2@example.com")
    _, token1 = await make_pat(db_session, user1, scopes=["inference:basic"])
    _, token2 = await make_pat(db_session, user2, scopes=["inference:basic"])

    await app.state.redis.set(f"rl:{user1.id}", test_settings.daily_request_limit)

    resp1 = await client.post(
        "/api/predict", json={"text": "x"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    resp2 = await client.post(
        "/api/predict", json={"text": "x"},
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert resp1.status_code == 429
    assert resp2.status_code == 200
