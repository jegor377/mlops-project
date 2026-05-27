import logging

from datetime import datetime, timezone
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from urllib.parse import urlencode

from src.ml_server.models.user import User
from src.ml_server.models.user_auth_method import UserAuthMethod, AuthProvider


logger = logging.getLogger(__name__)


async def flush(session: AsyncSession, redirect_uri: str) -> RedirectResponse | None:
    try:
        await session.flush()
        return None
    except IntegrityError as e:
        logger.error(f"IntegrityError during registration: {e.orig}")
        await session.rollback()
        error_redirect_uri = (
            redirect_uri
            + "?"
            + urlencode({"login-error": "Login failed"})
        )
        response = RedirectResponse(url=error_redirect_uri)
        return response
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error creating user: {e}")
        error_redirect_uri = (
            redirect_uri
            + "?"
            + urlencode({"login-error": "Internal server error"})
        )
        response = RedirectResponse(url=error_redirect_uri)
        return response


async def create_active_user(
    normalized_email: str,
    sub: str,
    redirect_uri: str,
    session: AsyncSession
) -> tuple[RedirectResponse | None, User]:
    user = User(
        email=normalized_email,
        is_active=True,
        activated_at=datetime.now(timezone.utc),
    )

    new_auth_method = UserAuthMethod(
        user=user,
        provider=AuthProvider.GOOGLE,
        provider_user_id=sub,
    )

    session.add(user)
    session.add(new_auth_method)
    return await flush(session, redirect_uri), user


async def try_creating_user_auth_method(
    user: User,
    sub: str,
    redirect_uri: str,
    session: AsyncSession
) -> RedirectResponse | None:
    stmt = select(UserAuthMethod).where(
        UserAuthMethod.user_id == user.id,
        UserAuthMethod.provider == AuthProvider.GOOGLE,
        UserAuthMethod.provider_user_id == sub,
    )
    result = await session.execute(stmt)
    auth_method = result.scalar_one_or_none()

    if not auth_method:
        new_auth_method = UserAuthMethod(
            user_id=user.id,
            provider=AuthProvider.GOOGLE,
            provider_user_id=sub,
        )

        session.add(new_auth_method)

        user.is_active = True
        user.activated_at = datetime.now(timezone.utc)

        return await flush(session, redirect_uri)
    return None
