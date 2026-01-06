from fastapi import FastAPI

from . import __version__
from .models.data_models import ModelRequest, ModelResponse
from .services.ml_model import Model

app = FastAPI()
model = Model()


@app.post("/predict", response_model=ModelResponse)
async def read_root(request: ModelRequest):
    response = model.predict([request.text])
    return ModelResponse(prediction=response[0])


@app.get("/ping")
async def ping():
    return "pong"


@app.get("/version")
async def get_version():
    return {"version": __version__}


@app.get("/")
async def root():
    return {"message": "Welcome to the ML model server!"}
