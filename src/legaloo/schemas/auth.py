from .base import CamelModel

# Request fields default to "" and are validated in auth_service, so the app gets
# the exact AuthValidator messages instead of generic Pydantic errors.


class RegisterRequest(CamelModel):
    name: str = ""
    email: str = ""
    password: str = ""


class LoginRequest(CamelModel):
    email: str = ""
    password: str = ""


class UserOut(CamelModel):
    id: str
    name: str
    email: str


class AuthResponse(CamelModel):
    token: str
    user: UserOut


class MeResponse(UserOut):
    daily_goal_minutes: int
