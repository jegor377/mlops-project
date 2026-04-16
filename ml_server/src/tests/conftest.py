import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from asgi_lifespan import LifespanManager

from src.ml_server.conf.settings import Settings
from src.ml_server.app import create_app
from src.ml_server.dependencies.db import get_session
from src.ml_server.models.base import Base
from src.ml_server.models import *  # noqa: F401, F403


test_settings = Settings()


@pytest_asyncio.fixture()
async def app():
    app = create_app(test_settings)
    async with LifespanManager(app):
        yield app


@pytest_asyncio.fixture()
async def engine():
    eng = create_async_engine(
        test_settings.db_uri,
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
        trans = await conn.begin()
        session_factory = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with session_factory() as session:
            try:
                yield session
            finally:
                await trans.rollback()


@pytest_asyncio.fixture
async def client(app, db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.pop(get_session, None)
