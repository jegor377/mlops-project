from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from sqlalchemy import select

from src.ml_server.models.user import User
from src.ml_server.models.user_auth_method import UserAuthMethod, AuthProvider
from src.tests.conftest import make_classic_user


GOOGLE_CALLBACK_URL = "/auth/login_via_google/callback"


# ---------------------------------------------------------------------------
# /auth/login_via_google/callback
# ---------------------------------------------------------------------------

GOOGLE_USER_INFO = {
    "sub": "118234567890123456789",
    "email": "igor@example.com",
    "email_verified": True,
}


def _mock_oauth(user_info: dict):
    """Return a mock oauth object that injects user_info into the callback."""
    mock_oauth = MagicMock()
    mock_oauth.google.authorize_access_token = AsyncMock(
        return_value={"userinfo": user_info}
    )
    return mock_oauth


async def test_google_callback_creates_new_user(client, app, db_session):
    app.state.oauth = _mock_oauth(GOOGLE_USER_INFO)
    response = await client.get(GOOGLE_CALLBACK_URL)

    assert response.status_code in (200, 307)

    result = await db_session.execute(
        select(User).where(User.email == GOOGLE_USER_INFO["email"])
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_active is True
    assert user.activated_at is not None

    result = await db_session.execute(
        select(UserAuthMethod).where(
            UserAuthMethod.user_id == user.id,
            UserAuthMethod.provider == AuthProvider.GOOGLE,
        )
    )
    assert result.scalar_one_or_none() is not None


async def test_google_callback_links_existing_classic_account(client, app, db_session):
    # Pre-existing unverified classic account
    existing_user = await make_classic_user(
        db_session,
        email=GOOGLE_USER_INFO["email"],
        is_active=False,
    )

    app.state.oauth = _mock_oauth(GOOGLE_USER_INFO)
    response = await client.get(GOOGLE_CALLBACK_URL)

    assert response.status_code in (200, 307)

    await db_session.refresh(existing_user)
    assert existing_user.is_active is True
    assert existing_user.activated_at is not None

    # Google auth method added
    result = await db_session.execute(
        select(UserAuthMethod).where(
            UserAuthMethod.user_id == existing_user.id,
            UserAuthMethod.provider == AuthProvider.GOOGLE,
        )
    )
    assert result.scalar_one_or_none() is not None


async def test_google_callback_missing_sub_returns_400(client, app, db_session):
    app.state.oauth = _mock_oauth({**GOOGLE_USER_INFO, "sub": None})
    response = await client.get(GOOGLE_CALLBACK_URL)
    assert response.status_code == 400


async def test_google_callback_unverified_email_returns_400(client, app, db_session):
    app.state.oauth = _mock_oauth({**GOOGLE_USER_INFO, "email_verified": False})
    response = await client.get(GOOGLE_CALLBACK_URL)
    assert response.status_code == 400


async def test_google_callback_deactivated_user_returns_401(client, app, db_session):
    user = await make_classic_user(
        db_session,
        email=GOOGLE_USER_INFO["email"]
    )
    user.deactivated_at = datetime.now(timezone.utc)
    await db_session.commit()

    app.state.oauth = _mock_oauth(GOOGLE_USER_INFO)
    response = await client.get(GOOGLE_CALLBACK_URL)

    assert response.status_code == 401
