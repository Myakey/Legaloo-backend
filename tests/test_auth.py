from datetime import UTC, datetime, timedelta

import jwt
import pytest
from conftest import BUDI_ID, FakeDB
from fastapi.testclient import TestClient

UNAUTHORIZED = {"detail": "Sesi berakhir, silakan masuk lagi", "field": None}


def _register(client: TestClient, **overrides: object):
    body = {"name": "Andi Wijaya", "email": "andi@legaloo.id", "password": "rahasia123"}
    body.update(overrides)
    return client.post("/auth/register", json=body)


def test_register_happy_path(client: TestClient, fake_db: FakeDB) -> None:
    r = _register(client, name="  Andi Wijaya ", email="  Andi@Legaloo.ID ")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["name"] == "Andi Wijaya"
    assert body["user"]["email"] == "andi@legaloo.id"
    assert body["token"]

    stored = next(u for u in fake_db.users.values() if u.name == "Andi Wijaya")
    assert stored.password_hash.startswith("$2b$12$")  # bcrypt, never plaintext

    me = client.get("/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.json() == {
        "id": stored.id,
        "name": "Andi Wijaya",
        "email": "andi@legaloo.id",
        "dailyGoalMinutes": 10,
    }


@pytest.mark.parametrize(
    ("overrides", "field", "message"),
    [
        ({"name": "   "}, "name", "Nama wajib diisi"),
        ({"name": "Al"}, "name", "Nama minimal 3 karakter"),
        ({"name": "Andi123"}, "name", "Nama hanya boleh berisi huruf dan spasi"),
        ({"email": ""}, "email", "Email wajib diisi"),
        ({"email": "andi@legaloo"}, "email", "Format email tidak valid"),
        ({"password": ""}, "password", "Kata sandi wajib diisi"),
        ({"password": "abc123"}, "password", "Kata sandi minimal 8 karakter"),
        (
            {"password": "abcdefgh"},
            "password",
            "Kata sandi harus berisi huruf dan angka",
        ),
        (
            {"password": "12345678"},
            "password",
            "Kata sandi harus berisi huruf dan angka",
        ),
        # first failing field wins: name before email before password
        ({"name": "", "email": "x", "password": ""}, "name", "Nama wajib diisi"),
        # Pydantic-level failures map to the same "wajib diisi" messages
        ({"name": None}, "name", "Nama wajib diisi"),
        ({"email": 123}, "email", "Email wajib diisi"),
    ],
)
def test_register_validation(
    client: TestClient, fake_db: FakeDB, overrides: dict, field: str, message: str
) -> None:
    r = _register(client, **overrides)
    assert r.status_code == 422
    assert r.json() == {"detail": message, "field": field}


def test_register_duplicate_email_is_case_insensitive(
    client: TestClient, fake_db: FakeDB
) -> None:
    r = _register(client, email="BUDI@legaloo.id")
    assert r.status_code == 409
    assert r.json() == {"detail": "Email sudah terdaftar", "field": "email"}


def test_login_happy_path(client: TestClient, fake_db: FakeDB) -> None:
    r = client.post(
        "/auth/login", json={"email": " Budi@Legaloo.id ", "password": "legaloo123"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user"] == {
        "id": BUDI_ID,
        "name": "Budi Santoso",
        "email": "budi@legaloo.id",
    }
    claims = jwt.decode(
        body["token"], "test-secret-test-secret-test-secret-123", algorithms=["HS256"]
    )
    assert claims["sub"] == BUDI_ID


@pytest.mark.parametrize(
    ("email", "password"),
    [("budi@legaloo.id", "salah123"), ("nobody@legaloo.id", "legaloo123")],
)
def test_login_wrong_credentials(
    client: TestClient, fake_db: FakeDB, email: str, password: str
) -> None:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 401
    assert r.json() == {"detail": "Email atau kata sandi salah", "field": None}


@pytest.mark.parametrize(
    ("body", "field", "message"),
    [
        (
            {"email": "budi@legaloo.id", "password": ""},
            "password",
            "Kata sandi wajib diisi",
        ),
        ({"email": "budi@legaloo.id"}, "password", "Kata sandi wajib diisi"),
        ({"email": "", "password": "x"}, "email", "Email wajib diisi"),
        ({"email": "budi", "password": "x"}, "email", "Format email tidak valid"),
    ],
)
def test_login_validation(
    client: TestClient, fake_db: FakeDB, body: dict, field: str, message: str
) -> None:
    r = client.post("/auth/login", json=body)
    assert r.status_code == 422
    assert r.json() == {"detail": message, "field": field}


def test_me(client: TestClient, auth: dict[str, str]) -> None:
    r = client.get("/me", headers=auth)
    assert r.status_code == 200
    assert r.json()["dailyGoalMinutes"] == 10


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer not-a-jwt"},
        {"Authorization": "Basic abc"},
        {
            "Authorization": "Bearer "
            + jwt.encode(
                {"sub": BUDI_ID, "exp": 9999999999},
                "wrong-secret-wrong-secret-wrong-secret-123",
            )
        },
        {
            "Authorization": "Bearer "
            + jwt.encode(
                {"sub": BUDI_ID, "exp": datetime.now(UTC) - timedelta(minutes=1)},
                "test-secret-test-secret-test-secret-123",
            )
        },
        {
            "Authorization": "Bearer "
            + jwt.encode(
                {"sub": "00000000-0000-4000-8000-999999999999", "exp": 9999999999},
                "test-secret-test-secret-test-secret-123",
            )
        },
    ],
    ids=["missing", "garbage", "basic", "wrong-secret", "expired", "deleted-user"],
)
def test_me_rejects_bad_tokens(
    client: TestClient, fake_db: FakeDB, headers: dict[str, str]
) -> None:
    r = client.get("/me", headers=headers)
    assert r.status_code == 401
    assert r.json() == UNAUTHORIZED
