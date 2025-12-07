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

def test_predict_speed():
    import time
    import numpy as np
    
    okay_time = 0.5 # seconds
    okay_percentile = 75 # percentile
    measurements = 100
    
    # Load the model once to avoid measuring load time
    response = client.post(
        "/predict",
        json={"text": "This is a load test sentence."}
    )
    
    measured_time = []
    for _ in range(measurements):
        start_time = time.time()
        response = client.post(
            "/predict",
            json={"text": "This is a test sentence to check the speed of prediction."}
        )
        end_time = time.time()
        assert response.status_code == 200
        measured_time.append(end_time - start_time)
    measured_time = np.array(measured_time)
    assert measured_time.mean() < okay_time  # Average time should be less than 0.5 seconds
    assert np.percentile(measured_time, okay_percentile) < okay_time  # 75th percentile should be less than 0.5 seconds
    

def test_missing_text_field():
    response = client.post("/predict", json={})
    assert response.status_code == 422  # Unprocessable Entity