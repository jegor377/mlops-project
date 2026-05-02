"""Tests for Personal Access Token endpoints."""
import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import secrets
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.models.user import User
from src.ml_server.models.user_session import UserSession


# ── Helpers ──────────────────────────────────────────────────────────────────

CREATE_URL = "/api/tokens"
LIST_URL = "/api/tokens"
PASSWORD = "StrongPass1!"


async def _make_user(session: AsyncSession, email: str = "igor@example.com") -> User:
    pw_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    user = User(email=email, password_hash=pw_hash, is_active=True)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _make_session(session: AsyncSession, user: User, expired: bool = False) -> UserSession:
    offset = timedelta(hours=-1 if expired else 24)
    us = UserSession(
        user_id=user.id,
        token=f"sess-{'exp' if expired else 'val'}-{user.id}",
        expires_at=datetime.now(timezone.utc) + offset,
    )
    session.add(us)
    await session.commit()
    await session.refresh(us)
    return us


async def _make_pat(
    session: AsyncSession,
    user: User,
    *,
    name: str = "Test Token",
    scopes: list[str] | None = None,
    expired: bool = False,
    is_active: bool = True,
) -> PersonalAccessToken:
    raw = "vlt_testtoken" + secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    offset = timedelta(days=-1 if expired else 90)
    pat = PersonalAccessToken(
        user_id=user.id,
        name=name,
        token_hash=token_hash,
        token_prefix="vlt_test",
        scopes=",".join(scopes or ["read:events"]),
        expires_at=datetime.now(timezone.utc) + offset,
        created_at=datetime.now(timezone.utc),
        is_active=is_active,
    )
    session.add(pat)
    await session.commit()
    await session.refresh(pat)
    return pat


VALID_BODY = {
    "name": "CI Pipeline",
    "scopes": ["read:events", "write:events"],
    "expires_in_days": 90,
}


# ── POST /api/tokens ──────────────────────────────────────────────────────────


async def test_create_pat_returns_201_and_raw_token(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.post(CREATE_URL, json=VALID_BODY)

    assert resp.status_code == 201
    data = resp.json()
    assert data["raw_token"].startswith("vlt_")
    assert len(data["raw_token"]) > 20
    assert data["name"] == VALID_BODY["name"]
    assert set(data["scopes"]) == set(VALID_BODY["scopes"])
    assert data["is_active"] is True
    assert "token_hash" not in data  # never expose hash


async def test_create_pat_raw_token_not_stored_plaintext(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.post(CREATE_URL, json=VALID_BODY)
    raw = resp.json()["raw_token"]

    result = await db_session.execute(select(PersonalAccessToken))
    pat = result.scalar_one()
    assert pat.token_hash != raw
    assert pat.token_hash == hashlib.sha256(raw.encode()).hexdigest()


async def test_create_pat_persists_in_db(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    await client.post(CREATE_URL, json=VALID_BODY)

    result = await db_session.execute(
        select(PersonalAccessToken).where(PersonalAccessToken.user_id == user.id)
    )
    pat = result.scalar_one_or_none()
    assert pat is not None
    assert pat.name == "CI Pipeline"
    assert pat.is_active is True


async def test_create_pat_with_no_expiry(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "expires_in_days": None}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 201
    assert resp.json()["expires_at"] is None


async def test_create_pat_invalid_scope_returns_422(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "scopes": ["read:events", "delete:everything"]}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 422


async def test_create_pat_empty_scopes_returns_422(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "scopes": []}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 422


async def test_create_pat_empty_name_returns_422(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "name": ""}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 422


async def test_create_pat_unauthenticated_returns_401(client, db_session):
    resp = await client.post(CREATE_URL, json=VALID_BODY)
    assert resp.status_code == 401


async def test_create_pat_expired_session_returns_401(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user, expired=True)
    client.cookies.set("session", us.token)

    resp = await client.post(CREATE_URL, json=VALID_BODY)
    assert resp.status_code == 401


async def test_create_pat_prefix_is_correct_length(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.post(CREATE_URL, json=VALID_BODY)
    data = resp.json()

    assert data["token_prefix"] == data["raw_token"][:8]


async def test_create_pat_scopes_deduplicated(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "scopes": ["read:events", "read:events", "read:events"]}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 201
    assert resp.json()["scopes"].count("read:events") == 1


# ── GET /api/tokens ───────────────────────────────────────────────────────────


async def test_list_pats_returns_only_own_tokens(client, db_session):
    user1 = await _make_user(db_session, "user1@example.com")
    user2 = await _make_user(db_session, "user2@example.com")
    us1 = await _make_session(db_session, user1)

    await _make_pat(db_session, user1, name="Token A")
    await _make_pat(db_session, user1, name="Token B")
    await _make_pat(db_session, user2, name="Token C")  # should NOT appear

    client.cookies.set("session", us1.token)
    resp = await client.get(LIST_URL)

    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()]
    assert "Token A" in names
    assert "Token B" in names
    assert "Token C" not in names


async def test_list_pats_empty_for_new_user(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get(LIST_URL)

    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_pats_includes_inactive_tokens(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    await _make_pat(db_session, user, name="Revoked", is_active=False)
    client.cookies.set("session", us.token)

    resp = await client.get(LIST_URL)

    assert resp.status_code == 200
    assert any(not t["is_active"] for t in resp.json())


async def test_list_pats_unauthenticated_returns_401(client, db_session):
    resp = await client.get(LIST_URL)
    assert resp.status_code == 401


async def test_list_pats_no_raw_token_in_response(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    await _make_pat(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get(LIST_URL)

    for pat in resp.json():
        assert "raw_token" not in pat
        assert "token_hash" not in pat


# ── DELETE /api/tokens/{id} ───────────────────────────────────────────────────


async def test_revoke_pat_returns_200(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    pat = await _make_pat(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.delete(f"/api/tokens/{pat.id}")

    assert resp.status_code == 200


async def test_revoke_pat_sets_is_active_false(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    pat = await _make_pat(db_session, user)
    client.cookies.set("session", us.token)

    await client.delete(f"/api/tokens/{pat.id}")
    await db_session.refresh(pat)

    assert pat.is_active is False


async def test_revoke_pat_not_found_returns_404(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.delete("/api/tokens/99999")

    assert resp.status_code == 404


async def test_revoke_pat_other_user_returns_404(client, db_session):
    """User cannot revoke another user's token."""
    user1 = await _make_user(db_session, "u1@example.com")
    user2 = await _make_user(db_session, "u2@example.com")
    us2 = await _make_session(db_session, user2)
    pat = await _make_pat(db_session, user1)  # belongs to user1
    client.cookies.set("session", us2.token)

    resp = await client.delete(f"/api/tokens/{pat.id}")

    assert resp.status_code == 404
    # Verify token still active
    await db_session.refresh(pat)
    assert pat.is_active is True


async def test_revoke_already_revoked_returns_409(client, db_session):
    user = await _make_user(db_session)
    us = await _make_session(db_session, user)
    pat = await _make_pat(db_session, user, is_active=False)
    client.cookies.set("session", us.token)

    resp = await client.delete(f"/api/tokens/{pat.id}")

    assert resp.status_code == 409


async def test_revoke_pat_unauthenticated_returns_401(client, db_session):
    resp = await client.delete("/api/tokens/1")
    assert resp.status_code == 401
