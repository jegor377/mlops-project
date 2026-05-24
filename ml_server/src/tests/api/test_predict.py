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
