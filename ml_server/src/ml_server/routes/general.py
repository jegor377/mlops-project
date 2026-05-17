from fastapi import APIRouter, Request, Depends
from typing import Annotated

from src.ml_server.dependencies.pat_token import get_pat
from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.schemas.llm import LLMRequest, LLMResponse


router = APIRouter()


@router.post("/api/predict", response_model=LLMResponse)
async def predict(
    request: LLMRequest,
    req: Request,
    pat: Annotated[PersonalAccessToken, Depends(get_pat(scopes=["inference:basic"]))],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LLMResponse:
    if settings.load_model:
        response = req.app.state.model.predict([request.text])
    else:
        response = [
            "This is a dummy prediction. Replace with actual model inference logic."
        ]
    return LLMResponse(prediction=response[0])


@router.get("/api/ping")
async def ping():
    return "pong"
