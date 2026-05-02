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
from src.ml_server.models.user_session import UserSession
from src.ml_server.models.password_reset import PasswordReset

from src.ml_server.schemas.user import UserCreate, UserLogin, ForgotPassword, ResetPassword

from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.current_user import get_current_user

from src.ml_server.services.email import send_verification_email, send_password_reset_email


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
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification link."
        )

    if verification.expires_at < datetime.now(timezone.utc):
        await session.delete(verification)
        await session.commit()
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification link."
        )

    result = await session.execute(select(User).where(User.id == verification.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification link."
        )

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


@router.post("/auth/login", status_code=200)
async def login(
    request: UserLogin,
    session: Annotated[AsyncSession, Depends(get_session)],
    req: Request,
):
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # Constant-time check even if user doesn't exist (prevent user enumeration)
    dummy_hash = "$2b$12$xHAznIgwigxdRMy6SN5KY.KrVqPfhKAxI7O6B.h28oAxffCGkJpLO"
    password_to_check = user.password_hash if user else dummy_hash

    password_valid = bcrypt.checkpw(
        request.password.encode("utf-8"),
        password_to_check.encode("utf-8"),
    )

    if not user or not password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account not yet activated. Please verify your email.",
        )

    # Issue session token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=req.app.state.settings.session_expire_hours
    )
    session_record = UserSession(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    session.add(session_record)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to persist session for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    secure = req.app.state.settings.env != "development"
    response = Response(status_code=200)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=secure,
        samesite="lax",
        expires=int(expires_at.timestamp()),
    )
    return response


@router.post("/auth/forgot-password", status_code=200)
async def forgot_password(
    request: ForgotPassword,
    session: Annotated[AsyncSession, Depends(get_session)],
    req: Request,
):
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # Always return 200 — never reveal whether the email exists
    if user is None or not user.is_active:
        return Response(status_code=200)

    # Invalidate any existing reset tokens for this user
    existing = await session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id)
    )
    for record in existing.scalars().all():
        await session.delete(record)

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=req.app.state.settings.password_reset_expire_hours
    )
    reset = PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    session.add(reset)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to persist password reset token for user {user.id}: {e}")
        return Response(status_code=200)  # Still don't leak anything

    try:
        token_url = req.app.state.settings.hostname
        token_url += "/reset-password"
        token_url += "?" + urlencode({"token": token})

        await send_password_reset_email(
            user.email,
            token_url,
            req.app.state.settings,
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")

    return Response(status_code=200)


@router.post("/auth/reset-password", status_code=200)
async def reset_password(
    request: ResetPassword,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(PasswordReset).where(PasswordReset.token == request.token)
    )
    reset = result.scalar_one_or_none()

    if reset is None or reset.expires_at < datetime.now(timezone.utc):
        if reset is not None:
            await session.delete(reset)
            await session.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    result = await session.execute(select(User).where(User.id == reset.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    password_hash = bcrypt.hashpw(request.new_password.encode("utf-8"), bcrypt.gensalt())
    user.password_hash = password_hash.decode("utf-8")
    await session.delete(reset)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to reset password for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return Response(status_code=200)


@router.get("/auth/me", status_code=200)
async def me(
    user: Annotated[User, Depends(get_current_user)],
):
    return {"email": user.email, "id": user.id}


@router.post("/auth/logout", status_code=200)
async def logout(request: Request, session: Annotated[AsyncSession, Depends(get_session)]):
    token = request.cookies.get("session")
    if token:
        result = await session.execute(select(UserSession).where(UserSession.token == token))
        user_session = result.scalar_one_or_none()
        if user_session:
            await session.delete(user_session)
            await session.commit()
    response = Response(status_code=200)
    response.delete_cookie("session")
    return response
