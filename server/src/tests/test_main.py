import pytest
from fastapi.testclient import TestClient

from ..server.main import app

client = TestClient(app)


def test_predict():
    data = {"text": "I love this product! It's amazing and works perfectly."}
    response = client.post("/predict", json=data)
    assert response.status_code == 200
    assert response.json() == {"prediction": "Very Positive"}


@pytest.mark.slow
def test_predict_speed():
    import time

    import numpy as np

    okay_time = 0.5  # seconds
    okay_percentile = 75  # percentile
    measurements = 100

    # Load the model once to avoid measuring load time
    data = {"text": "This is a load test sentence."}
    response = client.post("/predict", json=data)

    data = {"text": "This is a test to check the speed of prediction."}
    measured_time = []
    for _ in range(measurements):
        start_time = time.time()
        response = client.post("/predict", json=data)
        end_time = time.time()
        assert response.status_code == 200
        measured_time.append(end_time - start_time)
    measured_time = np.array(measured_time)
    m = measured_time.mean()
    s = measured_time.std()
    assert (
        measured_time.mean() < okay_time
    )  # Average time should be less than 0.5 seconds
    assert (
        np.percentile(measured_time, okay_percentile) < okay_time
    )  # 75th percentile should be less than 0.5 seconds
    assert (
        m + 3 * s < okay_time
    )  # 89% od the population measurements should be less than 0.5 seconds


def test_missing_text_field():
    response = client.post("/predict", json={})
    assert response.status_code == 422  # Unprocessable Entity


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.text == '"pong"'


def test_version():
    from ..server import __version__

    response = client.get("/version")
    assert response.status_code == 200
    resp = response.json()
    assert "version" in resp
    assert resp["version"] == __version__


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    resp = response.json()
    assert "message" in resp
    assert resp["message"] == "Welcome to the ML model server!"
