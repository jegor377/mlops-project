from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, ANY

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.password_reset import PasswordReset
from src.ml_server.models.user import User
from src.ml_server.models.user_auth_method import UserAuthMethod, AuthProvider

from src.tests.conftest import make_classic_user, LOGIN_PAYLOAD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FORGOT_URL = "/auth/forgot-password"
RESET_URL = "/auth/reset-password"
VALID_EMAIL = "igor@example.com"
NEW_PASSWORD = "NewStrongPass2!"


async def _create_reset_token(
    session: AsyncSession,
    user: User,
    *,
    expired: bool = False,
) -> PasswordReset:
    delta = timedelta(hours=-1) if expired else timedelta(hours=1)
    reset = PasswordReset(
        user_id=user.id,
        token="test-reset-token-abc123",
        expires_at=datetime.now(timezone.utc) + delta,
    )
    session.add(reset)
    await session.commit()
    await session.refresh(reset)
    return reset


# ---------------------------------------------------------------------------
# forgot-password
# ---------------------------------------------------------------------------


async def test_forgot_password_sends_email_for_existing_user(client, db_session):
    user = await make_classic_user(db_session)

    with patch(
        "src.ml_server.routes.auth.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await client.post(FORGOT_URL, json={"email": user.email})

    assert response.status_code == 200

    result = await db_session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id)
    )
    reset = result.scalar_one_or_none()
    assert reset is not None
    assert reset.expires_at > datetime.now(timezone.utc)

    mock_send.assert_awaited_once_with(user.email, ANY, ANY)


async def test_forgot_password_returns_200_for_unknown_email(client, db_session):
    """Never reveal whether an email is registered."""
    with patch(
        "src.ml_server.routes.auth.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await client.post(FORGOT_URL, json={"email": "ghost@example.com"})

    assert response.status_code == 200
    mock_send.assert_not_awaited()


async def test_forgot_password_returns_200_for_inactive_user(client, db_session):
    """Inactive (unverified) accounts should not receive reset emails."""
    user = await make_classic_user(
        db_session,
        email="inactive@example.com",
        is_active=False,
    )

    with patch(
        "src.ml_server.routes.auth.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await client.post(FORGOT_URL, json={"email": user.email})

    assert response.status_code == 200
    mock_send.assert_not_awaited()


async def test_forgot_password_invalidates_existing_token(client, db_session):
    """A second request must replace the old token, not accumulate tokens."""
    user = await make_classic_user(db_session)
    old_reset = await _create_reset_token(db_session, user)

    with patch("src.ml_server.routes.auth.send_password_reset_email", new_callable=AsyncMock):
        await client.post(FORGOT_URL, json={"email": user.email})

    result = await db_session.execute(
        select(PasswordReset).where(PasswordReset.token == old_reset.token)
    )
    assert result.scalar_one_or_none() is None

    result = await db_session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id)
    )
    resets = result.scalars().all()
    assert len(resets) == 1


async def test_forgot_password_email_failure_still_returns_200(client, db_session):
    """SMTP failure must not leak an error to the caller."""
    user = await make_classic_user(db_session)

    with patch(
        "src.ml_server.routes.auth.send_password_reset_email",
        new_callable=AsyncMock,
        side_effect=Exception("SMTP down"),
    ):
        response = await client.post(FORGOT_URL, json={"email": user.email})

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# reset-password
# ---------------------------------------------------------------------------


async def test_reset_password_updates_hash_and_deletes_token(client, db_session):
    import bcrypt

    user = await make_classic_user(db_session)
    reset = await _create_reset_token(db_session, user)

    response = await client.post(
        RESET_URL,
        json={"token": reset.token, "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 200
    
    await db_session.refresh(user)
    stmt = select(UserAuthMethod).where(
        UserAuthMethod.user_id == user.id,
        UserAuthMethod.provider == AuthProvider.CLASSIC,
        UserAuthMethod.provider_user_id == LOGIN_PAYLOAD["email"],
    )
    result = await db_session.execute(stmt)
    auth_method = result.scalar_one_or_none()
    assert bcrypt.checkpw(NEW_PASSWORD.encode(), auth_method.password_hash.encode())

    result = await db_session.execute(
        select(PasswordReset).where(PasswordReset.id == reset.id)
    )
    assert result.scalar_one_or_none() is None


async def test_reset_password_expired_token_returns_400(client, db_session):
    user = await make_classic_user(db_session)
    reset = await _create_reset_token(db_session, user, expired=True)

    response = await client.post(
        RESET_URL,
        json={"token": reset.token, "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 400


async def test_reset_password_expired_token_is_deleted(client, db_session):
    user = await make_classic_user(db_session)
    reset = await _create_reset_token(db_session, user, expired=True)

    await client.post(
        RESET_URL,
        json={"token": reset.token, "new_password": NEW_PASSWORD},
    )

    result = await db_session.execute(
        select(PasswordReset).where(PasswordReset.id == reset.id)
    )
    assert result.scalar_one_or_none() is None


async def test_reset_password_invalid_token_returns_400(client, db_session):
    response = await client.post(
        RESET_URL,
        json={"token": "does-not-exist", "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 400


async def test_reset_password_old_password_no_longer_works(client, db_session):
    import bcrypt

    user = await make_classic_user(db_session)
    reset = await _create_reset_token(db_session, user)

    await client.post(
        RESET_URL,
        json={"token": reset.token, "new_password": NEW_PASSWORD},
    )

    await db_session.refresh(user)
    stmt = select(UserAuthMethod).where(
        UserAuthMethod.user_id == user.id,
        UserAuthMethod.provider == AuthProvider.CLASSIC,
        UserAuthMethod.provider_user_id == LOGIN_PAYLOAD["email"],
    )
    result = await db_session.execute(stmt)
    auth_method = result.scalar_one_or_none()
    assert not bcrypt.checkpw(LOGIN_PAYLOAD["password"].encode(), auth_method.password_hash.encode())
