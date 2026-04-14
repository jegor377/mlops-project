from fastapi import APIRouter, Request

from src.ml_server.schemas.llm import LLMRequest, LLMResponse


router = APIRouter()


@router.post("/api/predict", response_model=LLMResponse)
async def predict(request: LLMRequest, req: Request):
    if req.app.state.settings.load_model:
        response = req.app.state.model.predict([request.text])
    else:
        response = [
            "This is a dummy prediction. Replace with actual model inference logic."
        ]
    return LLMResponse(prediction=response[0])


@router.get("/api/ping")
async def ping():
    return "pong"
