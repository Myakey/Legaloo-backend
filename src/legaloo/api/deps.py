from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.errors import MSG_UNAUTHORIZED, AppError
from ..core.security import decode_access_token
from ..repositories import user_repository
from ..repositories.user_repository import UserRow

# auto_error=False: we raise our own 401 with the app's message.
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UserRow:
    if creds is None or creds.scheme.lower() != "bearer":
        raise AppError(401, MSG_UNAUTHORIZED)
    user_id = decode_access_token(creds.credentials)
    user = await user_repository.get_by_id(user_id) if user_id else None
    if user is None:  # bad/expired token, or the account was deleted
        raise AppError(401, MSG_UNAUTHORIZED)
    return user


CurrentUser = Annotated[UserRow, Depends(get_current_user)]
