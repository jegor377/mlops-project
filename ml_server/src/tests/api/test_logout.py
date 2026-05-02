import bcrypt
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.user import User
from src.ml_server.models.user_session import UserSession


LOGOUT_URL = "/auth/logout"
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


async def _create_session(session: AsyncSession, user: User) -> UserSession:
    user_session = UserSession(
        user_id=user.id,
        token="test-session-token-abc123",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)
    return user_session


async def test_logout_returns_200(client, db_session):
    user = await _create_active_user(db_session)
    user_session = await _create_session(db_session, user)
    client.cookies.set("session", user_session.token)

    response = await client.post(LOGOUT_URL)

    assert response.status_code == 200


async def test_logout_deletes_session_from_db(client, db_session):
    user = await _create_active_user(db_session)
    user_session = await _create_session(db_session, user)
    client.cookies.set("session", user_session.token)

    await client.post(LOGOUT_URL)

    result = await db_session.execute(
        select(UserSession).where(UserSession.id == user_session.id)
    )
    assert result.scalar_one_or_none() is None


async def test_logout_clears_session_cookie(client, db_session):
    user = await _create_active_user(db_session)
    user_session = await _create_session(db_session, user)
    client.cookies.set("session", user_session.token)

    response = await client.post(LOGOUT_URL)

    # cookie cleared — either absent or set to empty/expired
    assert response.cookies.get("session") in (None, "")


async def test_logout_without_cookie_returns_200(client, db_session):
    """No session cookie — still 200, nothing to delete."""
    response = await client.post(LOGOUT_URL)

    assert response.status_code == 200


async def test_logout_with_invalid_token_returns_200(client, db_session):
    """Unknown token — still 200, no crash."""
    client.cookies.set("session", "totally-fake-token")

    response = await client.post(LOGOUT_URL)

    assert response.status_code == 200


async def test_logout_does_not_delete_other_user_sessions(client, db_session):
    """Only the presented token's session is removed."""
    user = await _create_active_user(db_session)
    target_session = await _create_session(db_session, user)

    other_session = UserSession(
        user_id=user.id,
        token="other-session-token-xyz",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(other_session)
    await db_session.commit()
    await db_session.refresh(other_session)

    client.cookies.set("session", target_session.token)
    await client.post(LOGOUT_URL)

    result = await db_session.execute(
        select(UserSession).where(UserSession.id == other_session.id)
    )
    assert result.scalar_one_or_none() is not None


async def test_login_then_logout_full_flow(client, db_session):
    """Login creates session, logout destroys it."""
    await _create_active_user(db_session)

    login_response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)
    assert login_response.status_code == 200
    assert "session" in login_response.cookies

    logout_response = await client.post(LOGOUT_URL)
    assert logout_response.status_code == 200

    result = await db_session.execute(select(UserSession))
    sessions = result.scalars().all()

    assert all(not s.token == login_response.cookies["session"] for s in sessions)
