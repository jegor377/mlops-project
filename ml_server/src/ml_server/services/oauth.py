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
    auth_provider: AuthProvider,
    session: AsyncSession
) -> tuple[RedirectResponse | None, User]:
    user = User(
        email=normalized_email,
        is_active=True,
        activated_at=datetime.now(timezone.utc),
    )

    new_auth_method = UserAuthMethod(
        user=user,
        provider=auth_provider,
        provider_user_id=sub,
    )

    session.add(user)
    session.add(new_auth_method)
    return await flush(session, redirect_uri), user


async def try_creating_user_auth_method(
    user: User,
    sub: str,
    redirect_uri: str,
    auth_provider: AuthProvider,
    session: AsyncSession
) -> RedirectResponse | None:
    stmt = select(UserAuthMethod).where(
        UserAuthMethod.user_id == user.id,
        UserAuthMethod.provider == auth_provider,
        UserAuthMethod.provider_user_id == sub,
    )
    result = await session.execute(stmt)
    auth_method = result.scalar_one_or_none()

    if not auth_method:
        new_auth_method = UserAuthMethod(
            user_id=user.id,
            provider=auth_provider,
            provider_user_id=sub,
        )

        session.add(new_auth_method)

        user.is_active = True
        user.activated_at = datetime.now(timezone.utc)

        return await flush(session, redirect_uri)
    return None


async def extract_oauth_profile(
    provider: str,
    client,
    oauth_token: dict,
) -> tuple[str | None, str | None]:
    """Returns (sub, email) for the given provider, or (None, None) on failure."""
    if provider == "google":
        user_info = oauth_token.get("userinfo") or {}
        sub = user_info.get("sub")
        email = user_info.get("email")
        if not user_info.get("email_verified", False):
            email = None
        return sub, email

    if provider == "github":
        profile = (await client.get("https://api.github.com/user", token=oauth_token)).json()
        raw_id = profile.get("id")
        sub = str(raw_id) if raw_id is not None else None
        email = profile.get("email")
        if not email:
            emails = (await client.get("https://api.github.com/user/emails", token=oauth_token)).json()
            primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            email = primary["email"] if primary else None
        return sub, email

    return None, None
