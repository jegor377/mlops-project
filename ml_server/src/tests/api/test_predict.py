async def test_ping(client):
    response = await client.get("/api/ping")
    assert response.status_code == 200


async def test_predict_dummy(client):
    response = await client.post("/api/predict", json={"text": "anything"})
    assert response.status_code == 200
    assert "prediction" in response.json()


async def test_predict_missing_field(client):
    response = await client.post("/api/predict", json={})
    assert response.status_code == 422
