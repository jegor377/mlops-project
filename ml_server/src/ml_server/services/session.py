from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from logging import Logger
from datetime import datetime, timezone, timedelta
from fastapi import Response, HTTPException
import secrets

from src.ml_server.conf.settings import Settings
from src.ml_server.models.user_session import UserSession


SESSION_TOKEN_LEN = 32


async def invalidate_session_by_user_id(
    session: AsyncSession,
    user_id: int,
) -> None:
    result = await session.execute(select(UserSession).where(UserSession.user_id == user_id))
    existing_session = result.scalar_one_or_none()
    if existing_session:
        await session.delete(existing_session)
        await session.commit()


async def invalidate_session_by_session_token(
    session: AsyncSession,
    token: str,
) -> None:
    result = await session.execute(select(UserSession).where(UserSession.token == token))
    user_session = result.scalar_one_or_none()
    if user_session:
        await session.delete(user_session)
        await session.commit()


async def issue_session_token(
    session: AsyncSession,
    session_expire_hours: int,
    user_id: int,
    logger: Logger,
) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(SESSION_TOKEN_LEN)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=session_expire_hours
    )
    session_record = UserSession(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    session.add(session_record)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to persist session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return token, expires_at


def set_session_cookie(
    response: Response,
    settings: Settings,
    token: str,
    expires_at: datetime
) -> None:
    secure = settings.env != "development"
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.session_expire_hours * 3600,
        expires=int(expires_at.timestamp()),
    )
