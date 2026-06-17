from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.ml_server.conf.settings import Settings
from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.rate_limit import check_rate_limit
from src.ml_server.dependencies.settings import get_settings
from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.models.user import User
from src.ml_server.models.audit_log import AuditLog, AuditCategory
from src.ml_server.dependencies.current_user import get_current_user
from src.ml_server.schemas.llm import LLMRequest, LLMResponse
from src.ml_server.schemas.audit_log import (
    AuditLogEntryResponse, AuditLogPageResponse
)
from src.ml_server.services.predict_metrics import record_req_metrics


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

    latency_ms: int = int((time.monotonic() - t0) * 1000)

    background_tasks.add_task(
        record_req_metrics,
        redis=req.app.state.redis,
        user_id=pat.user_id,
        latency_ms=latency_ms,
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


@router.get("/api/audit-log", response_model=AuditLogPageResponse)
async def list_audit_log(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: AuditCategory | None = Query(None),
) -> AuditLogPageResponse:
    base = select(AuditLog).where(AuditLog.user_id == user.id)

    if category is not None:
        base = base.where(AuditLog.category == category)

    total_result = await session.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = total_result.scalar_one()

    result = await session.execute(
        base.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = result.scalars().all()

    return AuditLogPageResponse(
        items=[
            AuditLogEntryResponse(
                id=e.id,
                event=e.event,
                ip=e.ip,
                user_agent=e.user_agent,
                metadata=e.extra_metadata,
                created_at=e.created_at.isoformat(),
            )
            for e in items
        ],
        total=total,
        page=page,
        size=size,
    )
