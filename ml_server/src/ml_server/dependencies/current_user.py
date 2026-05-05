from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import AsyncGenerator, Annotated

from src.ml_server.dependencies.db import get_session
from src.ml_server.models.user import User
from src.ml_server.models.user_session import UserSession


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[User, None]:
    """Resolve session cookie → User. Raises 401 if invalid/expired."""
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await session.execute(
        select(UserSession).where(UserSession.token == token)
    )
    user_session = result.scalar_one_or_none()

    if not user_session or user_session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await session.execute(
        select(User).where(User.id == user_session.user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    yield user
