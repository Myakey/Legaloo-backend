from conftest import FakeDB
from fastapi.testclient import TestClient


def _states(course: dict) -> list[str]:
    return [lv["state"] for lv in course["levels"]]


def test_courses_require_auth(client: TestClient, fake_db: FakeDB) -> None:
    for path in (
        "/courses",
        "/courses/1",
        "/me/progress",
        "/courses/1/levels/3/lesson",
    ):
        r = client.get(path)
        assert r.status_code == 401, path
        assert r.json()["detail"] == "Sesi berakhir, silakan masuk lagi"


def test_list_courses(client: TestClient, auth: dict[str, str]) -> None:
    r = client.get("/courses", headers=auth)
    assert r.status_code == 200
    courses = r.json()
    assert [c["id"] for c in courses] == [1, 2]
    c1 = courses[0]
    assert c1 == {
        "id": 1,
        "number": 1,
        "title": "Hak dan Kewajiban",
        "progress": 0.4,
        "unitLabel": "KURSUS 1, UNIT 2",
        "isCurrent": True,
        "levels": c1["levels"],
    }
    assert _states(c1) == ["COMPLETED", "COMPLETED", "ACTIVE", "LOCKED", "LOCKED"]
    assert set(c1["levels"][0]) == {"id", "type", "state", "title"}
    assert courses[1]["isCurrent"] is False
    assert _states(courses[1]) == ["COMPLETED", "ACTIVE", "LOCKED"]


def test_get_course_and_404(client: TestClient, auth: dict[str, str]) -> None:
    assert client.get("/courses/2", headers=auth).json()["progress"] == 0.33
    r = client.get("/courses/99", headers=auth)
    assert r.status_code == 404
    assert r.json() == {"detail": "Kursus tidak ditemukan", "field": None}


def test_progress(client: TestClient, auth: dict[str, str]) -> None:
    r = client.get("/me/progress", headers=auth)
    assert r.status_code == 200
    p = r.json()
    assert p["userName"] == "Budi Santoso"
    assert p["streakCount"] == 7
    assert p["minutesStudied"] == 6
    assert p["dailyGoalMinutes"] == 10
    assert p["currentCourseId"] == 1
    assert p["currentUnitNumber"] == 2
    assert [d["label"] for d in p["week"]] == ["S", "S", "R", "K", "J", "S", "M"]
    assert [d["completed"] for d in p["week"]] == [True, True] + [False] * 5


def test_lesson_active_level(client: TestClient, auth: dict[str, str]) -> None:
    r = client.get("/courses/1/levels/3/lesson", headers=auth)
    assert r.status_code == 200
    lesson = r.json()
    assert lesson["courseId"] == 1 and lesson["levelId"] == 3
    assert lesson["type"] == "LESSON"
    assert [s["kind"] for s in lesson["steps"]] == ["READ", "QUIZ"]
    read, quiz = lesson["steps"]
    assert read["modeLabel"] == "MODE BACA"
    assert read["content"] == {"paragraphs": ["a", "b"]}
    assert quiz["title"] is None
    assert quiz["mascotMessage"] == "Pilih jawabanmu!"
    assert len(quiz["content"]["options"]) == 4
    assert "feedbackCorrect" in quiz["content"]  # jsonb passed through unchanged


def test_lesson_completed_level_can_be_replayed(
    client: TestClient, auth: dict[str, str]
) -> None:
    assert client.get("/courses/1/levels/1/lesson", headers=auth).status_code == 200


def test_lesson_locked_and_unknown(client: TestClient, auth: dict[str, str]) -> None:
    r = client.get("/courses/1/levels/4/lesson", headers=auth)
    assert r.status_code == 403
    assert r.json() == {"detail": "Selesaikan level sebelumnya dulu ya!", "field": None}

    r = client.get("/courses/1/levels/42/lesson", headers=auth)
    assert r.status_code == 404
    assert r.json() == {"detail": "Level tidak ditemukan", "field": None}

    r = client.get("/courses/99/levels/1/lesson", headers=auth)
    assert r.status_code == 404
    assert r.json()["detail"] == "Kursus tidak ditemukan"


def test_complete_level(
    client: TestClient, auth: dict[str, str], fake_db: FakeDB
) -> None:
    r = client.post(
        "/courses/1/levels/3/complete",
        headers=auth,
        json={"correct": True, "minutesSpent": 4},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert _states(body["course"]) == ["COMPLETED"] * 3 + ["ACTIVE", "LOCKED"]
    assert body["course"]["progress"] == 0.6
    assert body["progress"]["minutesStudied"] == 10
    assert body["progress"]["streakCount"] == 8
    assert fake_db.recorded == [(1, 3, True, 4)]


def test_complete_clamps_minutes(
    client: TestClient, auth: dict[str, str], fake_db: FakeDB
) -> None:
    for minutes in (999, -5):
        r = client.post(
            "/courses/1/levels/1/complete",
            headers=auth,
            json={"correct": False, "minutesSpent": minutes},
        )
        assert r.status_code == 200
    assert [m for *_, m in fake_db.recorded] == [60, 0]


def test_complete_locked_level_is_rejected(
    client: TestClient, auth: dict[str, str], fake_db: FakeDB
) -> None:
    r = client.post(
        "/courses/1/levels/5/complete",
        headers=auth,
        json={"correct": True, "minutesSpent": 4},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Selesaikan level sebelumnya dulu ya!"
    assert fake_db.recorded == []


def test_complete_bad_body(client: TestClient, auth: dict[str, str]) -> None:
    r = client.post(
        "/courses/1/levels/3/complete", headers=auth, json={"minutesSpent": "banyak"}
    )
    assert r.status_code == 422
    assert r.json() == {"detail": "Data yang dikirim tidak valid", "field": None}


def test_unknown_route_uses_error_shape(client: TestClient) -> None:
    r = client.get("/nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Halaman tidak ditemukan", "field": None}
