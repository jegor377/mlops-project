from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, ANY

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.email_verification import EmailVerification
from src.ml_server.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/auth/register"
VERIFY_URL = "/api/auth/verify-email"
VALID_PAYLOAD = {"email": "igor@example.com", "password": "StrongPass1!"}


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

async def test_register_creates_inactive_user_and_sends_email(client, db_session):
    with patch(
        "src.ml_server.routes.auth.send_verification_email",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await client.post(REGISTER_URL, json=VALID_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert "user_id" in body
    assert "verify" in body["detail"].lower() or "email" in body["detail"].lower()

    # User persisted and inactive
    user = await db_session.get(User, body["user_id"])
    assert user is not None
    assert user.is_active is False

    # Verification token created
    result = await db_session.execute(
        select(EmailVerification).where(EmailVerification.user_id == user.id)
    )
    verification = result.scalar_one_or_none()
    assert verification is not None
    assert verification.expires_at > datetime.now(timezone.utc)

    mock_send.assert_awaited_once_with(VALID_PAYLOAD["email"], verification.token, ANY)


async def test_register_duplicate_email_returns_409(client, db_session):
    with patch("src.ml_server.routes.auth.send_verification_email", new_callable=AsyncMock):
        await client.post(REGISTER_URL, json=VALID_PAYLOAD)
        response = await client.post(REGISTER_URL, json=VALID_PAYLOAD)

    assert response.status_code == 409


async def test_register_email_send_failure_still_returns_201(client, db_session):
    """User is saved even when SMTP blows up — caller gets a warning detail."""

    with patch(
        "src.ml_server.routes.auth.send_verification_email",
        new_callable=AsyncMock,
        side_effect=Exception("SMTP down"),
    ):
        response = await client.post(REGISTER_URL, json=VALID_PAYLOAD)

    assert response.status_code == 201
    assert "could not be sent" in response.json()["detail"]


# ---------------------------------------------------------------------------
# verify-email
# ---------------------------------------------------------------------------

async def _create_user_and_token(
    session: AsyncSession,
    *,
    expired: bool = False,
) -> tuple[User, EmailVerification]:
    user = User(email="verify@example.com", password_hash="x", is_active=False)
    session.add(user)
    await session.flush()

    delta = timedelta(hours=-1) if expired else timedelta(hours=24)
    verification = EmailVerification(
        user_id=user.id,
        token="test-token-abc123",
        expires_at=datetime.now(timezone.utc) + delta,
    )
    session.add(verification)
    await session.commit()
    await session.refresh(user)
    await session.refresh(verification)
    return user, verification


async def test_verify_email_activates_user(client, db_session):
    user, verification = await _create_user_and_token(db_session)

    response = await client.get(VERIFY_URL, params={"token": verification.token})

    assert response.status_code == 200
    await db_session.refresh(user)
    assert user.is_active is True

    # Token must be deleted
    result = await db_session.execute(
        select(EmailVerification).where(EmailVerification.id == verification.id)
    )
    assert result.scalar_one_or_none() is None


async def test_verify_email_expired_token_returns_400(client, db_session):
    _, verification = await _create_user_and_token(db_session, expired=True)

    response = await client.get(VERIFY_URL, params={"token": verification.token})

    assert response.status_code == 400


async def test_verify_email_invalid_token_returns_400(client, db_session):
    response = await client.get(VERIFY_URL, params={"token": "does-not-exist"})

    assert response.status_code == 400
