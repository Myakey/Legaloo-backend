from fastapi import APIRouter

from ...schemas.auth import AuthResponse, LoginRequest, MeResponse, RegisterRequest
from ...services import auth_service
from ..deps import CurrentUser

router = APIRouter(tags=["auth"])


@router.post("/auth/register", status_code=201)
async def register(req: RegisterRequest) -> AuthResponse:
    return await auth_service.register(req)


@router.post("/auth/login")
async def login(req: LoginRequest) -> AuthResponse:
    return await auth_service.login(req)


@router.get("/me")
async def me(user: CurrentUser) -> MeResponse:
    return MeResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        daily_goal_minutes=user.daily_goal_minutes,
    )
