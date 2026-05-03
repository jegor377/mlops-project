from src.tests.conftest import make_user, make_session


ME_URL = "/auth/me"


# --- Tests ---

async def test_me_returns_user_data_for_valid_session(client, db_session):
    """Happy path: valid token returns 200 and user info."""
    user = await make_user(db_session)
    user_session = await make_session(db_session, user)
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
    user = await make_user(db_session)
    user_session = await make_session(db_session, user, expired=True)
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
    user = await make_user(db_session)
    user_session = await make_session(db_session, user)
    client.cookies.set("session", user_session.token)

    # Manually delete user but leave session
    await db_session.delete(user)
    await db_session.commit()

    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
