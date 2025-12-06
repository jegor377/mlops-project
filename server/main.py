from fastapi import FastAPI
from ml_model import Model
from data_models import ModelRequest
from data_models import ModelResponse


app = FastAPI()
model = Model()


@app.post("/predict", response_model=ModelResponse)
async def read_root(request: ModelRequest):
    response = model.predict([request.text])
    return ModelResponse(prediction=response[0])
