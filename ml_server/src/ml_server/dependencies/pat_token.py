from fastapi import Depends, HTTPException, Request
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from src.ml_server.models.pat import PersonalAccessToken
from src.ml_server.services.pat import hash_token
from src.ml_server.dependencies.db import get_session


def get_pat(scopes: list[str] | None = None):
    async def dependency(
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> PersonalAccessToken:
        raw_token = request.headers.get("Authorization")
        if not raw_token or not raw_token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")

        raw_token = raw_token[len("Bearer "):]
        token = hash_token(raw_token)

        result = await session.execute(
            select(PersonalAccessToken).where(
                PersonalAccessToken.token_hash == token
            )
        )
        pat = result.scalar_one_or_none()

        if not pat or (
            pat.expires_at and pat.expires_at < datetime.now(timezone.utc)
        ):
            raise HTTPException(status_code=401, detail="Not authenticated")

        if scopes:
            pat_scopes = set(pat.scopes.split(",") if pat.scopes else [])
            if not set(scopes).issubset(pat_scopes):
                raise HTTPException(status_code=403, detail="Insufficient scopes")

        return pat

    return dependency
