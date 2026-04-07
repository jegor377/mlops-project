from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI, Depends, Request, HTTPException
import os
from typing import Annotated, AsyncGenerator
import bcrypt
import logging

from . import __version__
from .models.data_models import ModelRequest, ModelResponse
from .models.user import Base, UserCreate, User
# from .services.ml_model import Model


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.logger = logging.getLogger(__name__)
    app.load_model = os.environ.get("LOAD_MODEL", "false").lower() == "true"
    # Load the ML model
    if app.load_model:
        app.state.model = Model()
    db_uri = os.environ["DB_URI"].replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_uri, pool_size=5, max_overflow=10)
    app.state.engine = engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.db = async_sessionmaker(engine, expire_on_commit=False)
    yield
    # Clean up the ML models and release the resources
    if app.load_model:
        del app.state.model
    await engine.dispose()
    

app = FastAPI(
    docs_url="/api/docs",
    lifespan=lifespan
)


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.db() as session:
        yield session


@app.post("/api/predict", response_model=ModelResponse)
async def read_root(request: ModelRequest):
    if app.load_model:
        response = app.state.model.predict([request.text])
    else:
        response = ["This is a dummy prediction. Replace with actual model inference logic."]
    return ModelResponse(prediction=response[0])


@app.get("/api/ping")
async def ping():
    return "pong"


@app.post("/api/auth/register", status_code=201)
async def register(request: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]):
    password_hash = bcrypt.hashpw(
        request.password.encode('utf-8'), 
        bcrypt.gensalt()
    )
    new_user = User(
        email=request.email,
        password_hash=password_hash.decode('utf-8'),
        is_active=False
    )
    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Registration failed")
    except Exception as e:
        await session.rollback()
        app.logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"user_id": new_user.id}
