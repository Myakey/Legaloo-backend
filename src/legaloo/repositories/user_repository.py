"""SQL for the `users` table."""

from dataclasses import dataclass

import asyncpg

from ..db.session import get_pool


@dataclass(frozen=True)
class UserRow:
    id: str
    name: str
    email: str
    password_hash: str
    daily_goal_minutes: int


class EmailTakenError(Exception):
    pass


_COLUMNS = "id::text, name, email, password_hash, daily_goal_minutes"


def _row(r: asyncpg.Record | None) -> UserRow | None:
    return UserRow(**dict(r)) if r is not None else None


async def get_by_email(email: str) -> UserRow | None:
    async with (await get_pool()).acquire() as conn:
        r = await conn.fetchrow(
            f"select {_COLUMNS} from users where lower(email) = lower($1)", email
        )
    return _row(r)


async def get_by_id(user_id: str) -> UserRow | None:
    async with (await get_pool()).acquire() as conn:
        r = await conn.fetchrow(
            f"select {_COLUMNS} from users where id = $1::uuid", user_id
        )
    return _row(r)


async def create(name: str, email: str, password_hash: str) -> UserRow:
    try:
        async with (await get_pool()).acquire() as conn:
            r = await conn.fetchrow(
                f"insert into users (name, email, password_hash) values ($1, $2, $3) "
                f"returning {_COLUMNS}",
                name,
                email,
                password_hash,
            )
    except asyncpg.UniqueViolationError as e:
        raise EmailTakenError(email) from e
    return UserRow(**dict(r))
