import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from redis.asyncio import Redis

from src.ml_server.conf.settings import Settings
from src.ml_server.routes.general import router as general_router
from src.ml_server.routes.auth import router as auth_router
from src.ml_server.routes.pat import router as pat_router
from src.ml_server.routes.audit_log import router as audit_log_router
from src.ml_server.services.ml_model import Model


def configure_google_oauth(oauth: OAuth, settings: Settings):
    oauth.register(
        name="google",
        client_id=settings.google_oauth2_creds.client_id,
        client_secret=settings.google_oauth2_creds.client_secret,
        authorize_url="https://accounts.google.com/o/oauth2/auth",
        authorize_params={"scope": "openid email profile"},
        access_token_url="https://oauth2.googleapis.com/token",
        client_kwargs={"scope": "openid email profile"},
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"
    )


def configure_github_oauth(oauth: OAuth, settings: Settings):
    oauth.register(
        name="github",
        client_id=settings.github_oauth2_creds.client_id,
        client_secret=settings.github_oauth2_creds.client_secret,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},  # needed for /user/emails
    )


def create_app(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.logger = logging.getLogger(__name__)
        # Load the ML model
        if settings.load_model:
            app.state.model = Model()
        engine = create_async_engine(
            settings.async_db_uri,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
        )
        app.state.engine = engine
        app.state.db = async_sessionmaker(engine, expire_on_commit=False)
        redis = Redis.from_url(str(settings.redis_uri), decode_responses=True)
        app.state.redis = redis
        oauth = OAuth()
        configure_google_oauth(oauth, settings)
        configure_github_oauth(oauth, settings)
        app.state.oauth = oauth
        yield
        # Clean up the ML models and release the resources
        if settings.load_model:
            del app.state.model
        await engine.dispose()

    is_secure = settings.env != "development"
    app = FastAPI(docs_url="/docs", lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.oauth_state_session_secret_key,
        session_cookie="oauth_state",  # avoid colliding with your auth session cookie
        max_age=300,  # OAuth state only needs to live for a few minutes
        https_only=is_secure,
        same_site="lax",
    )
    app.include_router(general_router)
    app.include_router(auth_router)
    app.include_router(pat_router)
    app.include_router(audit_log_router)
    return app
