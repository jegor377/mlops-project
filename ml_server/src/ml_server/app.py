from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi import FastAPI
import logging

from src.ml_server.conf.settings import Settings
from src.ml_server.routes.general import router as general_router
from src.ml_server.routes.auth import router as auth_router
from src.ml_server.services.ml_model import Model


def create_app(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.logger = logging.getLogger(__name__)
        app.state.settings = settings
        # Load the ML model
        if settings.load_model:
            app.state.model = Model()
        engine = create_async_engine(
            settings.db_uri,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
        )
        app.state.engine = engine
        app.state.db = async_sessionmaker(engine, expire_on_commit=False)
        yield
        # Clean up the ML models and release the resources
        if app.state.settings.load_model:
            del app.state.model
        await engine.dispose()

    app = FastAPI(docs_url="/docs", lifespan=lifespan)
    app.include_router(general_router)
    app.include_router(auth_router)
    return app
