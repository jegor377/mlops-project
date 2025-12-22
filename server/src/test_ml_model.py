import ml_model


def test_correct_prediction():
    model = ml_model.Model()
    texts = [
        "This is the worst experience I've ever had.",
        "It's a bad product.",
        "It's neutral.",
        "The product is good and meets my expectations.",
        "I love this product! It's amazing and works perfectly.",
    ]
    correct_predictions = [
        "Very Negative",
        "Negative",
        "Neutral",
        "Positive",
        "Very Positive",
    ]
    predictions = model.predict(texts)
    assert predictions == correct_predictions
