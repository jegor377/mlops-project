# routes/audit_log.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from typing import Annotated
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.audit_log import AuditLog, AuditCategory
from src.ml_server.models.user import User
from src.ml_server.dependencies.current_user import get_current_user
from src.ml_server.dependencies.db import get_session
from src.ml_server.schemas.audit_log import (
    AuditLogEntryResponse, AuditLogPageResponse
)


router = APIRouter()


@router.get("/audit-log", response_model=AuditLogPageResponse)
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
