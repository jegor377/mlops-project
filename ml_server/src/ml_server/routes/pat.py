import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.current_user import get_current_user
from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.models.user import User
from src.ml_server.schemas.pat import (
    PATCreate,
    PATCreateResponse,
    PATResponse,
    PATPage,
    PATStatus,
    PATStatsResponse,
    VALID_SCOPES,
)
from src.ml_server.services.pat import _hash_token

router = APIRouter()
logger = logging.getLogger(__name__)

TOKEN_PREFIX = "vlt_"


@router.post("/api/tokens", status_code=201, response_model=PATCreateResponse)
async def create_pat(
    body: PATCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> PATCreateResponse:
    """Create a new PAT. Returns raw token once — store it securely."""
    now = datetime.now(timezone.utc)
    pat_count_result = await session.execute(
        select(func.count())
        .select_from(PersonalAccessToken)
        .where(
            PersonalAccessToken.user_id == user.id
            and PersonalAccessToken.is_active
            and (PersonalAccessToken.expires_at is None
                 or PersonalAccessToken.expires_at > now)))
    pat_count = pat_count_result.scalar_one()
    if pat_count >= request.app.state.settings.pat_count_limit:
        raise HTTPException(
            status_code=400,
            detail=(
                f"PAT limit reached ({pat_count}/{request.app.state.settings.pat_count_limit}). "
                "Please revoke old tokens before creating new ones."
            ),
        )

    # Validate scopes
    invalid = set(body.scopes) - VALID_SCOPES
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid scopes: {sorted(invalid)}. Valid: {sorted(VALID_SCOPES)}",
        )
    if not body.scopes:
        raise HTTPException(status_code=422, detail="At least one scope required")

    # Generate token
    raw_token = TOKEN_PREFIX + secrets.token_urlsafe(40)
    token_hash = _hash_token(raw_token)
    token_prefix = raw_token[:8]  # "vlt_XXXX"

    now = datetime.now(timezone.utc)
    expires_at = None
    if body.expires_in_days is not None:
        expires_at = now + timedelta(days=body.expires_in_days)

    pat = PersonalAccessToken(
        user_id=user.id,
        name=body.name,
        token_hash=token_hash,
        token_prefix=token_prefix,
        scopes=",".join(sorted(set(body.scopes))),
        expires_at=expires_at,
        created_at=now,
        revoked_at=None,
        last_used_at=None,
        is_active=True,
    )
    session.add(pat)

    try:
        await session.commit()
        await session.refresh(pat)
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to create PAT for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return PATCreateResponse(
        id=pat.id,
        name=pat.name,
        token_prefix=pat.token_prefix,
        scopes=pat.scopes.split(","),
        expires_at=pat.expires_at,
        created_at=pat.created_at,
        revoked_at=pat.revoked_at,
        last_used_at=pat.last_used_at,
        is_active=pat.is_active,
        raw_token=raw_token,
    )


@router.get("/api/tokens", status_code=200, response_model=PATPage)
async def list_pats(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    status: PATStatus = Query(PATStatus.ALL, description="Filter tokens by status"),
    page: int = Query(1, gt=0, description="Page number (starting from 1)"),
    size: int = Query(20, gt=0, le=100, description="Number of tokens per page"),
) -> PATPage:
    """List all PATs for current user (active and inactive)."""

    now = datetime.now(timezone.utc)
    conditions = []

    if status == PATStatus.ALL:
        conditions.append(True)
    elif status == PATStatus.ACTIVE:
        conditions.append(
            and_(
                PersonalAccessToken.is_active,
                or_(
                    PersonalAccessToken.expires_at == None,  # noqa: E711
                    PersonalAccessToken.expires_at > now
                )
            )
        )
    elif status == PATStatus.INACTIVE:
        conditions.append(
            or_(
                PersonalAccessToken.is_active == False,  # noqa: E712
                and_(
                    PersonalAccessToken.expires_at != None,  # noqa: E711
                    PersonalAccessToken.expires_at <= now
                )
            )
        )

    result = await session.execute(
        select(PersonalAccessToken)
        .where(
            PersonalAccessToken.user_id == user.id,
            *conditions
        )
        .order_by(PersonalAccessToken.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    pats = result.scalars().all()
    return PATPage(
        items=[PATResponse.from_model(p) for p in pats],
        total=len(pats),
        page=page,
        size=size,
    )


@router.get("/api/tokens/stats", status_code=200, response_model=PATStatsResponse)
async def get_pat_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> PATStatsResponse:
    """Get statistics about PATs for current user."""

    now = datetime.now(timezone.utc)
    total_count = await session.execute(select(func.count()).where(
        PersonalAccessToken.user_id == user.id
    ))
    total_count = total_count.scalar_one()
    active_count = await session.execute(select(func.count()).where(
        PersonalAccessToken.user_id == user.id,
        PersonalAccessToken.is_active,
        or_(
            PersonalAccessToken.expires_at is None,
            PersonalAccessToken.expires_at > now
        )
    ))
    active_count = active_count.scalar_one()
    inactive_count = total_count - active_count

    return PATStatsResponse(
        total=total_count,
        active=active_count,
        inactive=inactive_count,
    )


@router.delete("/api/tokens/{token_id}", status_code=200)
async def revoke_pat(
    token_id: int,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Revoke (soft-delete) a PAT. Only owner can revoke."""
    result = await session.execute(
        select(PersonalAccessToken).where(
            PersonalAccessToken.id == token_id,
            PersonalAccessToken.user_id == user.id,
        )
    )
    pat = result.scalar_one_or_none()

    if not pat:
        raise HTTPException(status_code=404, detail="Token not found")

    if not pat.is_active:
        raise HTTPException(status_code=409, detail="Token already revoked")

    pat.is_active = False
    pat.revoked_at = datetime.now(timezone.utc)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to revoke PAT {token_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return Response(status_code=200)
