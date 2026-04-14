from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from fastapi import Request


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.db() as session:
        yield session
