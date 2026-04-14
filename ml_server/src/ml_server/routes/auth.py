from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import bcrypt
import logging

from src.ml_server.models.user import User
from src.ml_server.schemas.user import UserCreate
from src.ml_server.dependencies.db import get_session


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/auth/register", status_code=201)
async def register(
    request: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]
):
    password_hash = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt())
    new_user = User(
        email=request.email,
        password_hash=password_hash.decode("utf-8"),
        is_active=False,
    )
    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Registration failed")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"user_id": new_user.id}
