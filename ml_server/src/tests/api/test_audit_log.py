# tests/routes/test_audit_log.py
from __future__ import annotations

from datetime import datetime, timezone

from src.tests.conftest import make_classic_user, make_audit_log_entry, make_session


AUDIT_LOG_URL = "/audit-log"


# ── POST /audit-log (via service, not endpoint) ───────────────────────────
# The audit log has no write endpoint — entries are created by the service.
# We seed them directly via make_audit_log_entry in conftest.


# ── GET /audit-log ────────────────────────────────────────────────────────


async def test_list_audit_log_returns_own_entries(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)

    await make_audit_log_entry(db_session, user, event="pat.created")
    await make_audit_log_entry(db_session, user, event="auth.login")

    client.cookies.set("session", us.token)
    resp = await client.get(AUDIT_LOG_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert len(data["items"]) == 2


async def test_list_audit_log_does_not_return_other_users_entries(client, db_session):
    user1 = await make_classic_user(db_session, "u1@example.com")
    user2 = await make_classic_user(db_session, "u2@example.com")
    us1 = await make_session(db_session, user1)

    await make_audit_log_entry(db_session, user1, event="auth.login")
    await make_audit_log_entry(db_session, user2, event="auth.login")  # should NOT appear

    client.cookies.set("session", us1.token)
    resp = await client.get(AUDIT_LOG_URL)

    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_list_audit_log_empty_for_new_user(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get(AUDIT_LOG_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 20


async def test_list_audit_log_response_shape(client, db_session):
    """Every expected field is present and typed correctly."""
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    await make_audit_log_entry(
        db_session, user,
        event="pat.created",
        ip="10.0.0.1",
        user_agent="Mozilla/5.0",
        metadata={"token_name": "CI"},
    )
    client.cookies.set("session", us.token)

    resp = await client.get(AUDIT_LOG_URL)

    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["event"] == "pat.created"
    assert item["ip"] == "10.0.0.1"
    assert item["user_agent"] == "Mozilla/5.0"
    assert item["metadata"] == {"token_name": "CI"}
    assert "id" in item
    assert "created_at" in item
    datetime.fromisoformat(item["created_at"])  # must be valid ISO


async def test_list_audit_log_null_optional_fields(client, db_session):
    """ip, user_agent and metadata may all be None."""
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    await make_audit_log_entry(db_session, user, event="auth.logout", ip=None, user_agent=None)
    client.cookies.set("session", us.token)

    resp = await client.get(AUDIT_LOG_URL)

    item = resp.json()["items"][0]
    assert item["ip"] is None
    assert item["user_agent"] is None
    assert item["metadata"] is None


async def test_list_audit_log_ordered_newest_first(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)

    await make_audit_log_entry(db_session, user, event="auth.login",
                               created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    await make_audit_log_entry(db_session, user, event="pat.created",
                               created_at=datetime(2026, 6, 1, tzinfo=timezone.utc))
    client.cookies.set("session", us.token)

    resp = await client.get(AUDIT_LOG_URL)

    events = [i["event"] for i in resp.json()["items"]]
    assert events[0] == "pat.created"
    assert events[1] == "auth.login"


# ── Category filter ───────────────────────────────────────────────────────────


async def test_list_audit_log_filter_pat(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)

    await make_audit_log_entry(db_session, user, event="pat.created")
    await make_audit_log_entry(db_session, user, event="pat.revoked")
    await make_audit_log_entry(db_session, user, event="auth.login")

    client.cookies.set("session", us.token)
    resp = await client.get(AUDIT_LOG_URL, params={"category": "pat"})

    assert resp.status_code == 200
    events = [i["event"] for i in resp.json()["items"]]
    assert all(e.startswith("pat.") for e in events)
    assert "auth.login" not in events


async def test_list_audit_log_filter_auth(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)

    await make_audit_log_entry(db_session, user, event="auth.login")
    await make_audit_log_entry(db_session, user, event="auth.logout")
    await make_audit_log_entry(db_session, user, event="account.email_verified")

    client.cookies.set("session", us.token)
    resp = await client.get(AUDIT_LOG_URL, params={"category": "auth"})

    assert resp.status_code == 200
    events = [i["event"] for i in resp.json()["items"]]
    assert all(e.startswith("auth.") for e in events)
    assert "account.email_verified" not in events


async def test_list_audit_log_filter_account(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)

    await make_audit_log_entry(db_session, user, event="account.email_verified")
    await make_audit_log_entry(db_session, user, event="account.password_changed")
    await make_audit_log_entry(db_session, user, event="pat.created")

    client.cookies.set("session", us.token)
    resp = await client.get(AUDIT_LOG_URL, params={"category": "account"})

    assert resp.status_code == 200
    events = [i["event"] for i in resp.json()["items"]]
    assert all(e.startswith("account.") for e in events)
    assert "pat.created" not in events


async def test_list_audit_log_invalid_category_returns_422(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get(AUDIT_LOG_URL, params={"category": "nonexistent"})
    assert resp.status_code == 422


# ── Pagination ────────────────────────────────────────────────────────────────


async def test_list_audit_log_pagination(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)

    for i in range(15):
        await make_audit_log_entry(db_session, user, event="auth.login")

    client.cookies.set("session", us.token)

    resp = await client.get(AUDIT_LOG_URL, params={"page": 2, "size": 10})

    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["size"] == 10
    assert data["total"] == 15
    assert len(data["items"]) == 5


async def test_list_audit_log_invalid_pagination_returns_422(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get(AUDIT_LOG_URL, params={"page": 0, "size": 20})
    assert resp.status_code == 422

    resp = await client.get(AUDIT_LOG_URL, params={"page": 1, "size": 0})
    assert resp.status_code == 422

    resp = await client.get(AUDIT_LOG_URL, params={"page": 1, "size": 101})
    assert resp.status_code == 422


# ── Auth ──────────────────────────────────────────────────────────────────────


async def test_list_audit_log_unauthenticated_returns_401(client, db_session):
    resp = await client.get(AUDIT_LOG_URL)
    assert resp.status_code == 401


async def test_list_audit_log_expired_session_returns_401(client, db_session):
    user = await make_classic_user(db_session)
    us = await make_session(db_session, user, expired=True)
    client.cookies.set("session", us.token)

    resp = await client.get(AUDIT_LOG_URL)
    assert resp.status_code == 401
