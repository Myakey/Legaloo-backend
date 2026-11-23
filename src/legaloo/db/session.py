"""Lazily-created asyncpg pool, reused across invocations on a warm instance."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from ..core.config import get_settings

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            get_settings().database_url,
            min_size=1,
            max_size=4,
            # Supabase transaction pooler (port 6543) breaks prepared statements.
            statement_cache_size=0,
        )
    return _pool


@asynccontextmanager
async def transaction() -> AsyncIterator[asyncpg.Connection]:
    """One connection with an open transaction; commits on success, rolls back on error."""
    async with (await get_pool()).acquire() as conn, conn.transaction():
        yield conn
