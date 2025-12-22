from data_models import ModelRequest, ModelResponse
from fastapi import FastAPI
from ml_model import Model

app = FastAPI()
model = Model()


@app.post("/predict", response_model=ModelResponse)
async def read_root(request: ModelRequest):
    response = model.predict([request.text])
    return ModelResponse(prediction=response[0])


@app.get("/ping")
async def ping():
    return "pong"
