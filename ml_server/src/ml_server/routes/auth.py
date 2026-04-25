import bcrypt
import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from src.ml_server.models.user import User
from src.ml_server.models.email_verification import EmailVerification
from src.ml_server.schemas.user import UserCreate
from src.ml_server.dependencies.db import get_session

from src.ml_server.services.email import send_verification_email


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/auth/register", status_code=201)
async def register(
    request: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    req: Request,
):
    password_hash = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt())
    new_user = User(
        email=request.email,
        password_hash=password_hash.decode("utf-8"),
        is_active=False,
    )
    session.add(new_user)

    try:
        await session.flush()  # assigns new_user.id without committing yet
    except IntegrityError as e:
        logger.error(f"IntegrityError during registration: {e.orig}") 
        await session.rollback()
        raise HTTPException(status_code=409, detail="Registration failed")
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=req.app.state.settings.email_verification_expire_hours
    )
    verification = EmailVerification(
        user_id=new_user.id,
        token=token,
        expires_at=expires_at,
    )
    session.add(verification)

    try:
        await session.commit()
        await session.refresh(new_user)
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error saving verification token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    try:
        token_url = req.app.state.settings.hostname
        token_url += req.app.url_path_for("verify_email")
        token_url += "?" + urlencode({"token": token})
        
        await send_verification_email(
            new_user.email,
            token_url,
            req.app.state.settings,
        )
    except Exception as e:
        # User and token are persisted — they can be resent later.
        # Don't roll back or 500; just log and inform the caller.
        logger.error(f"Failed to send verification email to {new_user.email}: {e}")
        return Response(status_code=201)

    return Response(status_code=201)


@router.get("/auth/verify-email", status_code=200)
async def verify_email(
    token: Annotated[str, Query()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(EmailVerification).where(EmailVerification.token == token)
    )
    verification = result.scalar_one_or_none()

    if verification is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")

    if verification.expires_at < datetime.now(timezone.utc):
        await session.delete(verification)
        await session.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")

    result = await session.execute(
        select(User).where(User.id == verification.user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")

    user.is_active = True
    user.activated_at = datetime.now(timezone.utc)
    await session.delete(verification)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to activate user {verification.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"detail": "Email verified. Your account is now active."}
