from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import __version__
from .models.data_models import ModelRequest, ModelResponse
from .services.ml_model import Model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    app.state.model = Model()
    # Model warmup
    app.state.model.predict(["I hate this book!"])
    yield
    # Clean up the ML models and release the resources
    del app.state.model
    

app = FastAPI(lifespan=lifespan)


@app.post("/api/predict", response_model=ModelResponse)
async def read_root(request: ModelRequest):
    response = app.state.model.predict([request.text])
    return ModelResponse(prediction=response[0])


@app.get("/api/ping")
async def ping():
    return "pong"

