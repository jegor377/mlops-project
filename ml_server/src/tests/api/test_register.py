async def test_register_success(client):
    response = await client.post(
        "/api/auth/register",
        json={"email": "igor@example.com", "password": "securepass123"},
    )
    assert response.status_code == 201
    assert "user_id" in response.json()


async def test_register_duplicate_email(client):
    payload = {"email": "igor@example.com", "password": "securepass123"}
    await client.post("/api/auth/register", json=payload)
    # Second registration with same email
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


async def test_register_weak_password(client):
    response = await client.post(
        "/api/auth/register", json={"email": "igor@example.com", "password": "short"}
    )
    assert response.status_code == 422  # caught by Pydantic before hitting the route


async def test_register_invalid_email(client):
    response = await client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "securepass123"},
    )
    assert response.status_code == 422


async def test_register_missing_fields(client):
    response = await client.post("/api/auth/register", json={})
    assert response.status_code == 422


async def test_new_user_is_inactive(client, db_session):
    from sqlalchemy import select
    from src.ml_server.models.user import User

    await client.post(
        "/api/auth/register",
        json={"email": "igor@example.com", "password": "securepass123"},
    )
    result = await db_session.execute(
        select(User).where(User.email == "igor@example.com")
    )
    user = result.scalar_one()
    assert user.is_active is False
