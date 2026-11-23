from fastapi.testclient import TestClient

from legaloo.main import app


def test_health() -> None:
    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "ok"}
