import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_predict():
    response = client.post(
        "/predict",
        json={"text": "I love this product! It's amazing and works perfectly."}
    )
    assert response.status_code == 200
    assert response.json() == {"prediction": "Very Positive"}

def test_missing_text_field():
    response = client.post("/predict", json={})
    assert response.status_code == 422  # Unprocessable Entity