"""Password hashing (bcrypt) and access tokens (HS256 JWT).

bcrypt is deliberately slow CPU work, so the async wrappers run it in a thread
to keep the event loop free.
"""

import asyncio
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from .config import get_settings

_ALGORITHM = "HS256"


def _secret() -> str:
    secret = get_settings().jwt_secret
    if not secret:
        raise RuntimeError("JWT_SECRET is not set")
    return secret


async def hash_password(password: str) -> str:
    hashed = await asyncio.to_thread(
        bcrypt.hashpw, password.encode(), bcrypt.gensalt(rounds=12)
    )
    return hashed.decode()


async def verify_password(password: str, password_hash: str) -> bool:
    try:
        return await asyncio.to_thread(
            bcrypt.checkpw, password.encode(), password_hash.encode()
        )
    except ValueError:  # malformed hash in the database
        return False


def create_access_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=get_settings().jwt_expire_days),
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns the user id, or None if the token is invalid or expired."""
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None
