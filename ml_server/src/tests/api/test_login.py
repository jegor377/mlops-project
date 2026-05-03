from datetime import datetime, timezone
from sqlalchemy import select

from src.ml_server.models.user_session import UserSession
from src.tests.conftest import make_user, LOGIN_PAYLOAD


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

LOGIN_URL = "/auth/login"


async def test_login_returns_200_and_sets_session_cookie(client, db_session):
    await make_user(db_session)

    response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    assert response.status_code == 200
    assert "session" in response.cookies


async def test_login_creates_session_in_db(client, db_session):
    user = await make_user(db_session)

    await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    result = await db_session.execute(
        select(UserSession).where(UserSession.user_id == user.id)
    )
    session_record = result.scalar_one_or_none()
    assert session_record is not None
    assert session_record.expires_at > datetime.now(timezone.utc)


async def test_login_wrong_password_returns_401(client, db_session):
    await make_user(db_session)

    response = await client.post(
        LOGIN_URL, json={**LOGIN_PAYLOAD, "password": "WrongPass1!"}
    )

    assert response.status_code == 401


async def test_login_nonexistent_email_returns_401(client, db_session):
    response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    assert response.status_code == 401


async def test_login_unverified_user_returns_403(client, db_session):
    await make_user(db_session, is_active=False)

    response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    assert response.status_code == 403


async def test_login_does_not_set_cookie_on_failure(client, db_session):
    response = await client.post(LOGIN_URL, json=LOGIN_PAYLOAD)

    assert response.status_code == 401
    assert "session" not in response.cookies
