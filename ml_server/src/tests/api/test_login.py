from datetime import datetime, timezone
import bcrypt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.user import User

from src.ml_server.models.user_session import UserSession

# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

LOGIN_URL = "/auth/login"
LOGIN_PAYLOAD = {"email": "igor@example.com", "password": "StrongPass1!"}


async def _create_active_user(session: AsyncSession) -> User:
    password_hash = bcrypt.hashpw(
        LOGIN_PAYLOAD["password"].encode("utf-8"), bcrypt.gensalt()
    )
    user = User(
        email=LOGIN_PAYLOAD["email"],
        password_hash=password_hash.decode("utf-8"),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _create_inactive_user(session: AsyncSession) -> User:
    password_hash = bcrypt.hashpw(
        LOGIN_PAYLOAD["password"].encode("utf-8"), bcrypt.gensalt()
    )
    user = User(
        email=LOGIN_PAYLOAD["email"],
        password_hash=password_hash.decode("utf-8"),
        is_active=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def test_login_returns_200_and_sets_session_cookie(client, db_session):
    await _create_active_user(db_session)

    response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    assert response.status_code == 200
    assert "session" in response.cookies


async def test_login_creates_session_in_db(client, db_session):
    user = await _create_active_user(db_session)

    await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    result = await db_session.execute(
        select(UserSession).where(UserSession.user_id == user.id)
    )
    session_record = result.scalar_one_or_none()
    assert session_record is not None
    assert session_record.expires_at > datetime.now(timezone.utc)


async def test_login_wrong_password_returns_401(client, db_session):
    await _create_active_user(db_session)

    response = await client.post(
        LOGIN_URL, json={**LOGIN_PAYLOAD, "password": "WrongPass1!"}
    )

    assert response.status_code == 401


async def test_login_nonexistent_email_returns_401(client, db_session):
    response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    assert response.status_code == 401


async def test_login_unverified_user_returns_403(client, db_session):
    await _create_inactive_user(db_session)

    response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    assert response.status_code == 403


async def test_login_does_not_set_cookie_on_failure(client, db_session):
    response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    assert response.status_code == 401
    assert "session" not in response.cookies
