from __future__ import annotations

from collections.abc import AsyncGenerator

from pcg.storage.db import get_db


async def get_session() -> AsyncGenerator:
    async for session in get_db():
        yield session
