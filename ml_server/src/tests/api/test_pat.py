"""Tests for Personal Access Token endpoints."""
import hashlib
from sqlalchemy import select

from src.tests.conftest import make_user, make_pat, make_session
from src.ml_server.models.pat import PersonalAccessToken


# ── Helpers ──────────────────────────────────────────────────────────────────

CREATE_URL = "/api/tokens"
LIST_URL = "/api/tokens"


VALID_BODY = {
    "name": "CI Pipeline",
    "scopes": ["inference:basic"],
    "expires_in_days": 90,
}


# ── POST /api/tokens ──────────────────────────────────────────────────────────


async def test_create_pat_returns_201_and_raw_token(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
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
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.post(CREATE_URL, json=VALID_BODY)
    raw = resp.json()["raw_token"]

    result = await db_session.execute(select(PersonalAccessToken))
    pat = result.scalar_one()
    assert pat.token_hash != raw
    assert pat.token_hash == hashlib.sha256(raw.encode()).hexdigest()


async def test_create_pat_persists_in_db(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
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
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "expires_in_days": None}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 201
    assert resp.json()["expires_at"] is None


async def test_create_pat_invalid_scope_returns_422(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "scopes": ["inference:invalid"]}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 422


async def test_create_pat_empty_scopes_returns_422(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "scopes": []}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 422


async def test_create_pat_empty_name_returns_422(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "name": ""}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 422


async def test_create_pat_unauthenticated_returns_401(client, db_session):
    resp = await client.post(CREATE_URL, json=VALID_BODY)
    assert resp.status_code == 401


async def test_create_pat_expired_session_returns_401(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user, expired=True)
    client.cookies.set("session", us.token)

    resp = await client.post(CREATE_URL, json=VALID_BODY)
    assert resp.status_code == 401


async def test_create_pat_prefix_is_correct_length(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.post(CREATE_URL, json=VALID_BODY)
    data = resp.json()

    assert data["token_prefix"] == data["raw_token"][:8]


async def test_create_pat_scopes_deduplicated(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    body = {**VALID_BODY, "scopes": ["inference:basic", "inference:basic", "inference:basic"]}
    resp = await client.post(CREATE_URL, json=body)

    assert resp.status_code == 201
    assert resp.json()["scopes"].count("inference:basic") == 1


# ── GET /api/tokens ───────────────────────────────────────────────────────────


async def test_list_pats_returns_only_own_tokens(client, db_session):
    user1 = await make_user(db_session, "user1@example.com")
    user2 = await make_user(db_session, "user2@example.com")
    us1 = await make_session(db_session, user1)

    await make_pat(db_session, user1, name="Token A")
    await make_pat(db_session, user1, name="Token B")
    await make_pat(db_session, user2, name="Token C")  # should NOT appear

    client.cookies.set("session", us1.token)
    resp = await client.get(LIST_URL)

    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()["items"]]
    assert "Token A" in names
    assert "Token B" in names
    assert "Token C" not in names


async def test_list_pats_empty_for_new_user(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get(LIST_URL)

    assert resp.status_code == 200
    json_resp = resp.json()
    assert json_resp["items"] == []
    assert json_resp["total"] == 0
    assert json_resp["page"] == 1
    assert json_resp["size"] == 20


async def test_list_pats_includes_inactive_tokens(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    await make_pat(db_session, user, name="Revoked", is_active=False, is_revoked=True)
    client.cookies.set("session", us.token)

    resp = await client.get(LIST_URL)

    assert resp.status_code == 200
    resp_json = resp.json()
    assert any(not t["is_active"] for t in resp_json["items"])


async def test_list_pats_unauthenticated_returns_401(client, db_session):
    resp = await client.get(LIST_URL)
    assert resp.status_code == 401


async def test_list_pats_no_raw_token_in_response(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    await make_pat(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get(LIST_URL)

    resp_json = resp.json()
    for pat in resp_json["items"]:
        assert "raw_token" not in pat
        assert "token_hash" not in pat


async def test_list_pats_pagination(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)

    # Create 25 tokens
    for i in range(25):
        await make_pat(db_session, user, name=f"Token {i+1}")

    client.cookies.set("session", us.token)

    # Request page 3 with size 10
    resp = await client.get("/api/tokens?page=3&size=10")

    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["page"] == 3
    assert resp_json["size"] == 10
    assert len(resp_json["items"]) == 5  # only 5 items on page 3
    assert resp_json["total"] == 5  # total is number of items in this page, not total across all pages


async def test_list_pats_invalid_page_size_returns_422(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.get("/api/tokens?page=1&size=0")
    assert resp.status_code == 422

    resp = await client.get("/api/tokens?page=1&size=101")
    assert resp.status_code == 422


async def test_list_pats_status_filter(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)

    await make_pat(db_session, user, name="Active Token")
    await make_pat(db_session, user, name="Expired Token", expired=True)
    await make_pat(db_session, user, name="Revoked Token", is_active=False, is_revoked=True)

    client.cookies.set("session", us.token)

    # Test ACTIVE filter
    resp = await client.get("/api/tokens?status=active")
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()["items"]]
    assert "Active Token" in names
    assert "Expired Token" not in names
    assert "Revoked Token" not in names

    # Test INACTIVE filter
    resp = await client.get("/api/tokens?status=inactive")
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()["items"]]
    assert "Active Token" not in names
    assert "Expired Token" in names
    assert "Revoked Token" in names

    # Test ALL filter
    resp = await client.get("/api/tokens?status=all")
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()["items"]]
    assert "Active Token" in names
    assert "Expired Token" in names
    assert "Revoked Token" in names


# ── GET /api/tokens/stats ───────────────────────────────────────────────────


async def test_stats_endpoint_returns_correct_counts(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)

    # Create tokens with different statuses
    await make_pat(db_session, user, name="Active Token")
    await make_pat(db_session, user, name="Expired Token", expired=True)
    await make_pat(db_session, user, name="Revoked Token", is_active=False, is_revoked=True)

    client.cookies.set("session", us.token)

    resp = await client.get("/api/tokens/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["active"] == 1
    assert data["inactive"] == 2


# ── DELETE /api/tokens/{id} ───────────────────────────────────────────────────


async def test_revoke_pat_returns_200(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    pat, _ = await make_pat(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.delete(f"/api/tokens/{pat.id}")

    assert resp.status_code == 200


async def test_revoke_pat_sets_is_active_false(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    pat, _ = await make_pat(db_session, user)
    client.cookies.set("session", us.token)

    await client.delete(f"/api/tokens/{pat.id}")
    await db_session.refresh(pat)

    assert pat.is_active is False


async def test_revoke_pat_not_found_returns_404(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    client.cookies.set("session", us.token)

    resp = await client.delete("/api/tokens/99999")

    assert resp.status_code == 404


async def test_revoke_pat_other_user_returns_404(client, db_session):
    """User cannot revoke another user's token."""
    user1 = await make_user(db_session, "u1@example.com")
    user2 = await make_user(db_session, "u2@example.com")
    us2 = await make_session(db_session, user2)
    pat, _ = await make_pat(db_session, user1)  # belongs to user1
    client.cookies.set("session", us2.token)

    resp = await client.delete(f"/api/tokens/{pat.id}")

    assert resp.status_code == 404
    # Verify token still active
    await db_session.refresh(pat)
    assert pat.is_active is True


async def test_revoke_already_revoked_returns_409(client, db_session):
    user = await make_user(db_session)
    us = await make_session(db_session, user)
    pat, _ = await make_pat(db_session, user, is_active=False)
    client.cookies.set("session", us.token)

    resp = await client.delete(f"/api/tokens/{pat.id}")

    assert resp.status_code == 409


async def test_revoke_pat_unauthenticated_returns_401(client, db_session):
    resp = await client.delete("/api/tokens/1")
    assert resp.status_code == 401
