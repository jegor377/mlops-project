import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.current_user import get_current_user
from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.models.user import User
from src.ml_server.schemas.pat import (
    PATCreate,
    PATCreateResponse,
    PATResponse,
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
        last_used_at=pat.last_used_at,
        is_active=pat.is_active,
        raw_token=raw_token,
    )


@router.get("/api/tokens", status_code=200, response_model=list[PATResponse])
async def list_pats(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[PATResponse]:
    """List all PATs for current user (active and inactive)."""

    result = await session.execute(
        select(PersonalAccessToken)
        .where(PersonalAccessToken.user_id == user.id)
        .order_by(PersonalAccessToken.created_at.desc())
    )
    pats = result.scalars().all()
    return [PATResponse.from_model(p) for p in pats]


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

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to revoke PAT {token_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return Response(status_code=200)
