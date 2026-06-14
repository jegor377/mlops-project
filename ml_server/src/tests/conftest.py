import pytest_asyncio
import pytest
import bcrypt
import secrets
import hashlib
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from asgi_lifespan import LifespanManager
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.conf.settings import Settings
from src.ml_server.app import create_app
from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.settings import get_settings
from src.ml_server.models.base import Base
from src.ml_server.models import *  # noqa: F401, F403
from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.models.user import User
from src.ml_server.models.user_auth_method import UserAuthMethod, AuthProvider
from src.ml_server.models.user_session import UserSession
from src.ml_server.models.audit_log import AuditLog


LOGIN_PAYLOAD = {"email": "test@example.com", "password": "testpassword"}


@pytest.fixture
def test_settings():
    return Settings()


@pytest_asyncio.fixture()
async def app(test_settings):
    app = create_app(test_settings)
    async with LifespanManager(app):
        yield app


@pytest_asyncio.fixture()
async def engine(test_settings):
    eng = create_async_engine(
        test_settings.async_db_uri,
        pool_size=test_settings.pool_size,
        max_overflow=test_settings.max_overflow,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    async with engine.connect() as conn:
        async with conn.begin():
            async_session = async_sessionmaker(bind=conn, expire_on_commit=False)

            async with async_session() as session:
                yield session
                await session.rollback()


@pytest_asyncio.fixture
async def client(app, db_session, test_settings):
    async def override_get_session():
        yield db_session

    def override_get_settings():
        return test_settings

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = override_get_settings
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.pop(get_session, None)


async def make_classic_user(session: AsyncSession, email: str = LOGIN_PAYLOAD["email"], is_active: bool = True) -> User:
    pw_hash = bcrypt.hashpw(LOGIN_PAYLOAD["password"].encode(), bcrypt.gensalt()).decode()
    user = User(
        email=email,
        is_active=is_active
    )
    auth_method = UserAuthMethod(
        user=user,
        provider=AuthProvider.CLASSIC,
        provider_user_id=email,
        password_hash=pw_hash,
    )
    session.add(user)
    session.add(auth_method)
    await session.commit()
    await session.refresh(user)
    return user


async def make_session(session: AsyncSession, user: User, expired: bool = False) -> UserSession:
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


async def make_pat(
    session: AsyncSession,
    user: User,
    *,
    name: str = "Test Token",
    scopes: list[str] | None = None,
    expired: bool = False,
    is_active: bool = True,
    is_revoked: bool = False,
) -> tuple[PersonalAccessToken, str]:
    raw_token = "vlt_testtoken" + secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    offset = timedelta(days=-1 if expired else 90)
    pat = PersonalAccessToken(
        user_id=user.id,
        name=name,
        token_hash=token_hash,
        token_prefix="vlt_test",
        scopes=",".join(scopes or ["inference:basic"]),
        expires_at=datetime.now(timezone.utc) + offset,
        created_at=datetime.now(timezone.utc),
        revoked_at=None if not is_revoked else datetime.now(timezone.utc),
        last_used_at=None,
        is_active=is_active,
    )
    session.add(pat)
    await session.commit()
    await session.refresh(pat)
    return pat, raw_token


async def make_audit_log_entry(
    session: AsyncSession,
    user: "User",
    *,
    event: str = "auth.login",
    ip: str | None = "127.0.0.1",
    user_agent: str | None = "pytest/1.0",
    metadata: dict | None = None,
    created_at: datetime | None = None,
) -> AuditLog:
    from src.ml_server.models.audit_log import AuditLog, EVENT_CATEGORY

    category = EVENT_CATEGORY[event]
    entry = AuditLog(
        user_id=user.id,
        event=event,
        category=category,
        ip=ip,
        user_agent=user_agent,
        extra_metadata=metadata,
        created_at=created_at or datetime.now(timezone.utc),
    )
    session.add(entry)
    await session.flush()
    return entry
