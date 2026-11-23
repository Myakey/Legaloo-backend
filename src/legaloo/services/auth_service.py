"""Register / login. Validation mirrors the app's viewmodel/AuthValidator.kt exactly."""

import re

from ..core import security
from ..core.errors import AppError
from ..repositories import user_repository
from ..repositories.user_repository import EmailTakenError, UserRow
from ..schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut

_NAME_RE = re.compile(r"^[A-Za-z .'-]+$")
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"[0-9]")

MSG_LOGIN_FAILED = "Email atau kata sandi salah"
MSG_EMAIL_TAKEN = "Email sudah terdaftar"


def _invalid(message: str, field: str) -> AppError:
    return AppError(422, message, field)


def validate_name(name: str) -> None:
    if not name:
        raise _invalid("Nama wajib diisi", "name")
    if len(name) < 3:
        raise _invalid("Nama minimal 3 karakter", "name")
    if not _NAME_RE.match(name):
        raise _invalid("Nama hanya boleh berisi huruf dan spasi", "name")


def validate_email(email: str) -> None:
    if not email:
        raise _invalid("Email wajib diisi", "email")
    if not _EMAIL_RE.match(email):
        raise _invalid("Format email tidak valid", "email")


def validate_new_password(password: str) -> None:
    if not password:
        raise _invalid("Kata sandi wajib diisi", "password")
    if len(password) < 8:
        raise _invalid("Kata sandi minimal 8 karakter", "password")
    if not (_HAS_LETTER.search(password) and _HAS_DIGIT.search(password)):
        raise _invalid("Kata sandi harus berisi huruf dan angka", "password")


def _response(user: UserRow) -> AuthResponse:
    return AuthResponse(
        token=security.create_access_token(user.id),
        user=UserOut(id=user.id, name=user.name, email=user.email),
    )


async def register(req: RegisterRequest) -> AuthResponse:
    name = req.name.strip()
    email = req.email.strip().lower()
    validate_name(name)
    validate_email(email)
    validate_new_password(req.password)

    if await user_repository.get_by_email(email) is not None:
        raise AppError(409, MSG_EMAIL_TAKEN, "email")
    password_hash = await security.hash_password(req.password)
    try:
        user = await user_repository.create(name, email, password_hash)
    except EmailTakenError:  # lost a race with a concurrent registration
        raise AppError(409, MSG_EMAIL_TAKEN, "email") from None
    return _response(user)


async def login(req: LoginRequest) -> AuthResponse:
    email = req.email.strip()
    validate_email(email)
    if not req.password:
        raise _invalid("Kata sandi wajib diisi", "password")

    user = await user_repository.get_by_email(email)
    if user is None or not await security.verify_password(
        req.password, user.password_hash
    ):
        raise AppError(401, MSG_LOGIN_FAILED, None)
    return _response(user)
