"""One error shape for the whole API: {"detail": "<pesan>", "field": <str|null>}.

The Android app shows `detail` under the named form field, or as a form-level
error when `field` is null. Messages are user-facing, so they're in Indonesian.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger(__name__)

MSG_UNAUTHORIZED = "Sesi berakhir, silakan masuk lagi"
MSG_COURSE_NOT_FOUND = "Kursus tidak ditemukan"
MSG_LEVEL_NOT_FOUND = "Level tidak ditemukan"
MSG_LEVEL_LOCKED = "Selesaikan level sebelumnya dulu ya!"
MSG_INVALID_DATA = "Data yang dikirim tidak valid"
MSG_NOT_FOUND = "Halaman tidak ditemukan"
MSG_SERVER_ERROR = "Terjadi kesalahan pada server, coba lagi nanti"

# Used when Pydantic rejects an auth field outright (missing, null, wrong type):
# treat it as blank so the app sees the same message AuthValidator would show.
_BLANK_FIELD_MESSAGES = {
    "name": "Nama wajib diisi",
    "email": "Email wajib diisi",
    "password": "Kata sandi wajib diisi",
}


class AppError(Exception):
    def __init__(self, status_code: int, detail: str, field: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.field = field


def _body(detail: str, field: str | None = None) -> dict[str, str | None]:
    return {"detail": detail, "field": field}


async def _app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(_body(exc.detail, exc.field), status_code=exc.status_code)


async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 401:
        detail = MSG_UNAUTHORIZED
    elif exc.status_code == 404:
        detail = MSG_NOT_FOUND
    elif exc.status_code >= 500:
        detail = MSG_SERVER_ERROR
    else:
        detail = MSG_INVALID_DATA
    return JSONResponse(_body(detail), status_code=exc.status_code, headers=exc.headers)


async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Report the first error. Never leak Pydantic's English text to the app.
    for err in exc.errors():
        loc = err.get("loc", ())
        field = loc[-1] if loc and loc[0] == "body" else None
        if field in _BLANK_FIELD_MESSAGES:
            return JSONResponse(
                _body(_BLANK_FIELD_MESSAGES[field], field), status_code=422
            )
        break
    return JSONResponse(_body(MSG_INVALID_DATA), status_code=422)


async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error", exc_info=exc)
    return JSONResponse(_body(MSG_SERVER_ERROR), status_code=500)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unhandled)
