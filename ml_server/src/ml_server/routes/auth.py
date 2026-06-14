import bcrypt
import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from src.ml_server.conf.settings import Settings
from src.ml_server.models.user import User
from src.ml_server.models.user_auth_method import UserAuthMethod, AuthProvider
from src.ml_server.models.email_verification import EmailVerification
from src.ml_server.models.password_reset import PasswordReset
from src.ml_server.models.audit_log import EventCategory

from src.ml_server.schemas.user import UserCreate, UserLogin, ForgotPassword, ResetPassword

from src.ml_server.dependencies.settings import get_settings
from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.current_user import get_current_user

from src.ml_server.services.email import send_verification_email, send_password_reset_email
from src.ml_server.services.session import (
    issue_session_token,
    set_session_cookie,
    invalidate_session_by_user_id,
    invalidate_session_by_session_token
)
import src.ml_server.services.oauth as oauth_services
from src.ml_server.services.audit_log import log_event

from src.ml_server.utils.frontend_urls import FrontendURLs


router = APIRouter()
logger = logging.getLogger(__name__)
PASSWORD_ACTION_TOKEN_LEN = 32


@router.post("/auth/register", status_code=201)
async def register(
    request: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    req: Request,
):
    normalized_email = request.email.lower().strip()
    password_hash = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt())
    new_user = User(
        email=normalized_email,
        is_active=False,
    )
    new_auth_method = UserAuthMethod(
        provider=AuthProvider.CLASSIC,
        provider_user_id=normalized_email,
        password_hash=password_hash.decode("utf-8"),
    )
    new_user.auth_methods.append(new_auth_method)
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

    token = secrets.token_urlsafe(PASSWORD_ACTION_TOKEN_LEN)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.email_verification_expire_hours
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
        token_url = settings.hostname
        token_url += req.app.url_path_for("verify_email")
        token_url += "?" + urlencode({"token": token})

        await send_verification_email(
            new_user.email,
            token_url,
            settings,
        )
    except Exception as e:
        # User and token are persisted — they can be resent later.
        # Don't roll back or 500; just log and inform the caller.
        logger.error(f"Failed to send verification email to {new_user.email}: {e}")
        return Response(status_code=201)

    return Response(status_code=201)


@router.post("/auth/resend-verification", status_code=200)
async def resend_verification(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[User, Depends(get_current_user)],
    req: Request,
):
    # Already active — nothing to do, but don't leak state differences
    if user.is_active:
        return Response(status_code=200)

    # Check for an unexpired token — don't spam the user
    existing_result = await session.execute(
        select(EmailVerification).where(EmailVerification.user_id == user.id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        if existing.expires_at > datetime.now(timezone.utc):
            # Still valid — silently do nothing (frontend shows generic "check inbox")
            return Response(status_code=200)
        # Expired — delete it and issue a fresh one
        await session.delete(existing)

    token = secrets.token_urlsafe(PASSWORD_ACTION_TOKEN_LEN)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.email_verification_expire_hours
    )
    verification = EmailVerification(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    session.add(verification)

    await log_event(
        db=session,
        user_id=user.id,
        event=EventCategory.account_verification_resent,
        request=req,
    )

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to persist resend verification token for user {user.id}: {e}")
        return Response(status_code=200)

    try:
        token_url = settings.hostname
        token_url += req.app.url_path_for("verify_email")
        token_url += "?" + urlencode({"token": token})

        await send_verification_email(user.email, token_url, settings)
    except Exception as e:
        logger.error(f"Failed to resend verification email to {user.email}: {e}")

    return Response(status_code=200)


@router.get("/auth/verify-email", status_code=200)
async def verify_email(
    token: Annotated[str, Query()],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    req: Request,
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

    await log_event(
        db=session,
        user_id=user.id,
        event=EventCategory.account_email_verified,
        request=req,
    )

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to activate user {verification.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    login_uri = settings.frontend_hostname
    login_uri += FrontendURLs.LOGIN
    login_uri += "?" + urlencode({"just-activated": "true"})

    return RedirectResponse(url=login_uri)


@router.post("/auth/login", status_code=200)
async def login(
    request: UserLogin,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    req: Request,
):
    normalized_email = request.email.lower().strip()
    stmt = (
        select(UserAuthMethod)
        .options(selectinload(UserAuthMethod.user))
        .where(
            UserAuthMethod.provider == AuthProvider.CLASSIC,
            UserAuthMethod.provider_user_id == normalized_email,
        )
    )
    result = await session.execute(stmt)
    auth_method = result.scalar_one_or_none()

    # Constant-time check even if user doesn't exist (prevent user enumeration)
    dummy_hash = "$2b$12$xHAznIgwigxdRMy6SN5KY.KrVqPfhKAxI7O6B.h28oAxffCGkJpLO"
    password_to_check = (
        auth_method.password_hash
        if auth_method and auth_method.password_hash
        else dummy_hash
    )

    password_valid = bcrypt.checkpw(
        request.password.encode("utf-8"),
        password_to_check.encode("utf-8"),
    )

    if (not auth_method) or (not password_valid) or (auth_method.user.deactivated_at is not None):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    # Invalidate existing session
    await invalidate_session_by_user_id(
        session,
        auth_method.user.id
    )

    # Issue session token
    token, expires_at = await issue_session_token(
        session,
        settings.session_expire_hours,
        auth_method.user.id,
        req.app.state.logger
    )

    await log_event(
        db=session,
        user_id=auth_method.user.id,
        event=EventCategory.auth_login,
        request=req,
    )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    response = Response(status_code=200)
    set_session_cookie(response, settings, token, expires_at)
    return response


@router.post("/auth/forgot-password", status_code=200)
async def forgot_password(
    request: ForgotPassword,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    req: Request,
):
    normalized_email = request.email.lower().strip()
    stmt = (
        select(UserAuthMethod)
        .options(selectinload(UserAuthMethod.user))
        .where(
            UserAuthMethod.provider == AuthProvider.CLASSIC,
            UserAuthMethod.provider_user_id == normalized_email,
        )
    )
    result = await session.execute(stmt)
    auth_method = result.scalar_one_or_none()

    # Always return 200 — never reveal whether the email exists
    if auth_method is None or not auth_method.user.is_active:
        return Response(status_code=200)

    # Invalidate any existing reset tokens for this user
    existing = await session.execute(
        select(PasswordReset).where(PasswordReset.user_id == auth_method.user_id)
    )
    for record in existing.scalars().all():
        await session.delete(record)

    token = secrets.token_urlsafe(PASSWORD_ACTION_TOKEN_LEN)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.password_reset_expire_hours
    )
    reset = PasswordReset(
        user_id=auth_method.user_id,
        token=token,
        expires_at=expires_at,
    )
    session.add(reset)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to persist password reset token for user {auth_method.user_id}: {e}")
        return Response(status_code=200)  # Still don't leak anything

    try:
        token_url = settings.hostname
        token_url += req.app.url_path_for("reset_password")
        token_url += "?" + urlencode({"token": token})

        await send_password_reset_email(
            auth_method.user.email,
            token_url,
            settings,
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {auth_method.user.email}: {e}")

    return Response(status_code=200)


@router.post("/auth/reset-password", status_code=200)
async def reset_password(
    request: ResetPassword,
    session: Annotated[AsyncSession, Depends(get_session)],
    req: Request,
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

    stmt = (
        select(UserAuthMethod)
        .options(selectinload(UserAuthMethod.user))
        .where(
            UserAuthMethod.provider == AuthProvider.CLASSIC,
            UserAuthMethod.user_id == reset.user_id,
        )
    )
    result = await session.execute(stmt)
    auth_method = result.scalar_one_or_none()
    if auth_method is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    password_hash = bcrypt.hashpw(request.new_password.encode("utf-8"), bcrypt.gensalt())
    auth_method.password_hash = password_hash.decode("utf-8")
    await session.delete(reset)

    await log_event(
        db=session,
        user_id=auth_method.user.id,
        event=EventCategory.account_password_changed,
        request=req,
    )

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to reset password for user {auth_method.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return Response(status_code=200)


@router.get("/auth/me", status_code=200)
async def me(
    user: Annotated[User, Depends(get_current_user)],
):
    return {
        "email": user.email,
        "id": user.id,
        "is_active": user.is_active
    }


@router.post("/auth/logout", status_code=200)
async def logout(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    token = request.cookies.get("session")
    if token:
        user_id = await invalidate_session_by_session_token(
            session,
            token
        )
        if user_id != -1:
            await log_event(
                db=session,
                user_id=user_id,
                event=EventCategory.auth_logout,
                request=request,
            )
        await session.commit()
    response = Response(status_code=200)
    response.delete_cookie("session")
    return response


@router.get("/auth/login_via/{provider}")
async def auth_oauth(
    req: Request,
    provider: str,
    settings: Annotated[Settings, Depends(get_settings)]
):
    SUPPORTED_PROVIDERS = frozenset({"google", "github"})

    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404)

    redirect_uri = settings.hostname
    redirect_uri += req.app.url_path_for("oauth_callback", provider=provider)

    oauth = req.app.state.oauth
    client = getattr(oauth, provider)
    return await client.authorize_redirect(req, redirect_uri=redirect_uri)


@router.get("/auth/login_via/{provider}/callback")
async def oauth_callback(
    req: Request,
    provider: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)]
):
    if provider not in ("google", "github"):
        raise HTTPException(status_code=404)

    redirect_uri = settings.frontend_hostname + FrontendURLs.LOGIN
    error = req.query_params.get("error")
    if error:
        return RedirectResponse(
            url=redirect_uri + "?" + urlencode({"error": f"{provider}_login_cancelled"})
        )

    oauth = req.app.state.oauth
    client = getattr(oauth, provider)
    oauth_token = await client.authorize_access_token(req)

    # Normalize profile across providers
    sub, email = await oauth_services.extract_oauth_profile(
        provider,
        client,
        oauth_token
    )

    if not sub or not email:
        return RedirectResponse(
            url=redirect_uri + "?" + urlencode({"login-error": f"Incomplete profile from {provider.title()}"})
        )

    normalized_email = email.lower().strip()
    auth_provider = AuthProvider[provider.upper()]  # AuthProvider.GOOGLE / AuthProvider.GITHUB

    # Fetch user from the DB
    stmt = (
        select(User)
        .where(User.email == normalized_email)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    try:
        user = await oauth_services.handle_oauth_user_provisioning(
            session, user, normalized_email, sub, redirect_uri, auth_provider
        )
    except IntegrityError as e:
        logger.error(f"IntegrityError during registration: {e.orig}")
        await session.rollback()
        return RedirectResponse(url=redirect_uri + "?" + urlencode({"login-error": "Login failed"}))
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error creating user: {e}")
        return RedirectResponse(url=redirect_uri + "?" + urlencode({"login-error": "Internal server error"}))

    if user.deactivated_at is not None:
        redirect_uri += "?" + urlencode({"login-error": "Login failed"})
        response = RedirectResponse(url=redirect_uri)
        return response

    await log_event(
        db=session,
        user_id=user.id,
        event=EventCategory.auth_oauth_login,
        request=req,
    )

    # Invalidate existing session
    await invalidate_session_by_user_id(
        session,
        user.id
    )

    # Issue session token
    session_token, expires_at = await issue_session_token(
        session,
        settings.session_expire_hours,
        user.id,
        req.app.state.logger
    )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    redirect_uri = settings.frontend_hostname
    redirect_uri += FrontendURLs.DASHBOARD

    response = RedirectResponse(url=redirect_uri)
    set_session_cookie(response, settings, session_token, expires_at)
    return response
