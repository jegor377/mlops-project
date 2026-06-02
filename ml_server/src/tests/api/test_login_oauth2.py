import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from sqlalchemy import select

from src.ml_server.models.user import User
from src.ml_server.models.user_auth_method import UserAuthMethod, AuthProvider
from src.tests.conftest import make_classic_user


TEST_EMAIL = "igor@example.com"

GOOGLE_CALLBACK_URL = "/auth/login_via/google/callback"
GITHUB_CALLBACK_URL = "/auth/login_via/github/callback"

GOOGLE_USER_INFO = {
    "sub": "118234567890123456789",
    "email": TEST_EMAIL,
    "email_verified": True,
}

GITHUB_PROFILE = {
    "id": 987654321,
    "email": TEST_EMAIL,
}

GITHUB_EMAILS = [
    {"email": TEST_EMAIL, "primary": True, "verified": True},
]


def _mock_google_oauth(user_info: dict):
    mock_oauth = MagicMock()
    mock_oauth.google.authorize_access_token = AsyncMock(
        return_value={"userinfo": user_info}
    )
    return mock_oauth


def _mock_github_oauth(profile: dict, emails: list | None = None):
    mock_oauth = MagicMock()
    mock_client = MagicMock()

    async def mock_get(url, **kwargs):
        response = MagicMock()
        response.json.return_value = emails or [] if "emails" in url else profile
        return response

    mock_client.authorize_access_token = AsyncMock(return_value={"access_token": "tok"})
    mock_client.get = mock_get
    mock_oauth.github = mock_client
    return mock_oauth


# Each entry: (callback_url, oauth_mock, auth_provider)
PROVIDER_PARAMS = [
    pytest.param(
        GOOGLE_CALLBACK_URL,
        _mock_google_oauth(GOOGLE_USER_INFO),
        AuthProvider.GOOGLE,
        id="google",
    ),
    pytest.param(
        GITHUB_CALLBACK_URL,
        _mock_github_oauth(GITHUB_PROFILE),
        AuthProvider.GITHUB,
        id="github",
    ),
]


# ---------------------------------------------------------------------------
# Shared provider tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("callback_url, oauth_mock, auth_provider", PROVIDER_PARAMS)
async def test_oauth_callback_creates_new_user(client, app, db_session, callback_url, oauth_mock, auth_provider):
    app.state.oauth = oauth_mock
    response = await client.get(callback_url)

    assert response.status_code in (200, 307)

    result = await db_session.execute(select(User).where(User.email == TEST_EMAIL))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_active is True
    assert user.activated_at is not None

    result = await db_session.execute(
        select(UserAuthMethod).where(
            UserAuthMethod.user_id == user.id,
            UserAuthMethod.provider == auth_provider,
        )
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.parametrize("callback_url, oauth_mock, auth_provider", PROVIDER_PARAMS)
async def test_oauth_callback_links_existing_classic_account(client, app, db_session, callback_url, oauth_mock, auth_provider):
    existing_user = await make_classic_user(db_session, email=TEST_EMAIL, is_active=False)

    app.state.oauth = oauth_mock
    await client.get(callback_url)

    await db_session.refresh(existing_user)
    assert existing_user.is_active is True
    assert existing_user.activated_at is not None

    result = await db_session.execute(
        select(UserAuthMethod).where(
            UserAuthMethod.user_id == existing_user.id,
            UserAuthMethod.provider == auth_provider,
        )
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.parametrize("callback_url, oauth_mock, auth_provider", PROVIDER_PARAMS)
async def test_oauth_callback_deactivated_user_redirects_with_error(
    client,
    app,
    db_session,
    callback_url,
    oauth_mock,
    auth_provider
):
    user = await make_classic_user(db_session, email=TEST_EMAIL)
    user.deactivated_at = datetime.now(timezone.utc)
    await db_session.commit()

    app.state.oauth = oauth_mock

    response = await client.get(callback_url, follow_redirects=False)

    assert response.status_code == 307
    assert "login-error=Login+failed" in response.headers["location"]


# ---------------------------------------------------------------------------
# Google-specific tests
# ---------------------------------------------------------------------------

async def test_google_callback_missing_sub_redirects_with_error(client, app, db_session):
    app.state.oauth = _mock_google_oauth({**GOOGLE_USER_INFO, "sub": None})

    response = await client.get(GOOGLE_CALLBACK_URL, follow_redirects=False)

    assert response.status_code == 307
    assert "login-error=Incomplete+profile+from+Google" in response.headers["location"]


async def test_google_callback_unverified_email_redirects_with_error(client, app, db_session):
    app.state.oauth = _mock_google_oauth({**GOOGLE_USER_INFO, "email_verified": False})

    response = await client.get(GOOGLE_CALLBACK_URL, follow_redirects=False)

    assert response.status_code == 307
    assert "login-error=Incomplete+profile+from+Google" in response.headers["location"]


# ---------------------------------------------------------------------------
# GitHub-specific tests
# ---------------------------------------------------------------------------

async def test_github_callback_creates_new_user_with_hidden_email(client, app, db_session):
    app.state.oauth = _mock_github_oauth({**GITHUB_PROFILE, "email": None}, emails=GITHUB_EMAILS)
    response = await client.get(GITHUB_CALLBACK_URL)

    assert response.status_code in (200, 307)

    result = await db_session.execute(select(User).where(User.email == TEST_EMAIL))
    assert result.scalar_one_or_none() is not None


async def test_github_callback_missing_id_redirects_with_error(client, app, db_session):
    app.state.oauth = _mock_github_oauth({**GITHUB_PROFILE, "id": None})

    response = await client.get(GITHUB_CALLBACK_URL, follow_redirects=False)

    assert response.status_code == 307
    assert "login-error=Incomplete+profile+from+Github" in response.headers["location"]


async def test_github_callback_no_verified_email_redirects_with_error(client, app, db_session):
    profile_no_email = {**GITHUB_PROFILE, "email": None}
    unverified_emails = [{"email": TEST_EMAIL, "primary": True, "verified": False}]
    app.state.oauth = _mock_github_oauth(profile_no_email, emails=unverified_emails)

    response = await client.get(GITHUB_CALLBACK_URL, follow_redirects=False)

    assert response.status_code == 307
    assert "login-error=Incomplete+profile+from+Github" in response.headers["location"]
