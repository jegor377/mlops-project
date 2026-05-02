import bcrypt
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.user import User
from src.ml_server.models.user_session import UserSession

ME_URL = "/auth/me"
LOGIN_PAYLOAD = {"email": "igor@example.com", "password": "StrongPass1!"}

# --- Helpers (Reused from your logout logic) ---


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


async def _create_session(session: AsyncSession, user: User, expired: bool = False) -> UserSession:
    # If expired is True, set the time to 1 hour in the past
    offset = -1 if expired else 24
    user_session = UserSession(
        user_id=user.id,
        token=f"test-token-{'expired' if expired else 'valid'}",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=offset),
    )
    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)
    return user_session


# --- Tests ---

async def test_me_returns_user_data_for_valid_session(client, db_session):
    """Happy path: valid token returns 200 and user info."""
    user = await _create_active_user(db_session)
    user_session = await _create_session(db_session, user)
    client.cookies.set("session", user_session.token)

    response = await client.get(ME_URL)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["id"] == user.id


async def test_me_no_cookie_returns_401(client, db_session):
    """Fails if the session cookie is missing."""
    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


async def test_me_expired_session_returns_401(client, db_session):
    """Fails if the session exists in DB but has expired."""
    user = await _create_active_user(db_session)
    user_session = await _create_session(db_session, user, expired=True)
    client.cookies.set("session", user_session.token)

    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


async def test_me_invalid_token_returns_401(client, db_session):
    """Fails if the token does not exist in the database."""
    client.cookies.set("session", "non-existent-token")

    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


async def test_me_user_deleted_returns_401(client, db_session):
    """Edge case: session exists but the associated user was deleted."""
    user = await _create_active_user(db_session)
    user_session = await _create_session(db_session, user)
    client.cookies.set("session", user_session.token)

    # Manually delete user but leave session
    await db_session.delete(user)
    await db_session.commit()

    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
