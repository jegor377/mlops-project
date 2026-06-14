from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.conf.settings import Settings
from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.rate_limit import check_rate_limit
from src.ml_server.dependencies.settings import get_settings
from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.schemas.llm import LLMRequest, LLMResponse
from src.ml_server.services.request_log import record_request

router = APIRouter()


@router.post("/api/predict", response_model=LLMResponse)
async def predict(
    body: LLMRequest,
    req: Request,
    background_tasks: BackgroundTasks,
    pat: Annotated[PersonalAccessToken, Depends(check_rate_limit)],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    t0 = time.monotonic()

    if settings.load_model:
        prediction = req.app.state.model.predict([body.text])[0]
    else:
        prediction = "This is a dummy prediction. Replace with actual model inference logic."

    latency_ms = int((time.monotonic() - t0) * 1000)

    forwarded = req.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else (
        req.client.host if req.client else None
    )

    background_tasks.add_task(
        record_request,
        session,
        user_id=pat.user_id,
        pat_id=pat.id,
        method="POST",
        path="/api/predict",
        status_code=200,
        latency_ms=latency_ms,
        ip=ip,
    )

    return Response(
        content=LLMResponse(prediction=prediction).model_dump_json(),
        media_type="application/json",
        headers={
            "X-RateLimit-Limit": str(req.state.rl_limit),
            "X-RateLimit-Remaining": str(req.state.rl_remaining),
        },
    )


@router.get("/api/ping")
async def ping() -> str:
    return "pong"
