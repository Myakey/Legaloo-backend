"""Test fixtures. No test may reach a real database or the Gemini API.

- Settings come from env vars set here (they override .env), with a bogus DATABASE_URL.
- `asyncpg.create_pool` is replaced so any accidental DB access fails loudly.
- `fake_db` swaps the repository functions for an in-memory store. It mirrors the
  state rules from db/queries.sql closely enough to test the services and routes;
  the SQL itself is verified by the smoke test against Supabase.
"""

import os
from collections.abc import Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

os.environ.update(
    DATABASE_URL="postgresql://test:test@127.0.0.1:1/blocked",
    GEMINI_API_KEY="test-key",
    JWT_SECRET="test-secret-test-secret-test-secret-123",
    JWT_EXPIRE_DAYS="30",
)

from legaloo.core.config import get_settings
from legaloo.db import session
from legaloo.main import app
from legaloo.repositories import (
    course_repository,
    lesson_repository,
    progress_repository,
    user_repository,
)
from legaloo.repositories.course_repository import CourseState, LevelState
from legaloo.repositories.lesson_repository import StepRow
from legaloo.repositories.progress_repository import DayRow, StudyStats
from legaloo.repositories.user_repository import EmailTakenError, UserRow

BUDI_ID = "11111111-1111-4111-8111-111111111111"
# Precomputed bcrypt (cost 4) of "legaloo123" so tests stay fast.
BUDI_HASH = "$2b$04$gsXnlLSlxtS2cLB0ELcB0e4BSpqSADKdRLUsrF52ejVZTRnENAooa"


@pytest.fixture(autouse=True)
def _isolate(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    get_settings.cache_clear()

    async def _no_db(*_: Any, **__: Any) -> None:
        raise RuntimeError("tests must not touch the database")

    monkeypatch.setattr("asyncpg.create_pool", _no_db)
    monkeypatch.setattr(session, "_pool", None)
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------- fake repositories

COURSES = {
    1: ("Hak dan Kewajiban", 2, "KURSUS 1, UNIT 2", ["LESSON"] * 4 + ["PRACTICE"]),
    2: ("Aturan Sekolah", 1, "KURSUS 2, UNIT 1", ["LESSON", "LESSON", "PRACTICE"]),
}


@dataclass
class FakeDB:
    users: dict[str, UserRow] = field(default_factory=dict)
    # (course_id, position) -> completion order; higher = more recent
    completions: dict[tuple[str, int, int], int] = field(default_factory=dict)
    minutes_today: dict[str, int] = field(default_factory=dict)
    past_streak: dict[str, int] = field(default_factory=dict)  # days met before today
    recorded: list[tuple[Any, ...]] = field(default_factory=list)
    _clock: int = 0

    def complete(self, uid: str, course_id: int, pos: int) -> None:
        self._clock += 1
        self.completions[(uid, course_id, pos)] = self._clock

    # --- user_repository
    async def get_by_email(self, email: str) -> UserRow | None:
        return next(
            (u for u in self.users.values() if u.email.lower() == email.lower()), None
        )

    async def get_by_id(self, user_id: str) -> UserRow | None:
        return self.users.get(user_id)

    async def create(self, name: str, email: str, password_hash: str) -> UserRow:
        if await self.get_by_email(email):
            raise EmailTakenError(email)
        uid = f"00000000-0000-4000-8000-{len(self.users):012d}"
        self.users[uid] = UserRow(uid, name, email, password_hash, 10)
        return self.users[uid]

    # --- course_repository
    def _courses(self, uid: str) -> list[CourseState]:
        done = {(c, p): t for (u, c, p), t in self.completions.items() if u == uid}
        unfinished = [
            cid
            for cid, (_, _, _, types) in COURSES.items()
            if any((cid, i + 1) not in done for i in range(len(types)))
        ]
        recent = sorted(done.items(), key=lambda kv: -kv[1])
        current = next(
            (c for (c, _), _ in recent if c in unfinished),
            unfinished[0] if unfinished else 1,
        )
        out = []
        for cid, (title, unit, label, types) in COURSES.items():
            first_open = next(
                (i + 1 for i in range(len(types)) if (cid, i + 1) not in done), None
            )
            levels = [
                LevelState(
                    id=i + 1,
                    type=t,
                    title=f"Level {i + 1}",
                    state="COMPLETED"
                    if (cid, i + 1) in done
                    else "ACTIVE"
                    if i + 1 == first_open
                    else "LOCKED",
                )
                for i, t in enumerate(types)
            ]
            n_done = sum(lv.state == "COMPLETED" for lv in levels)
            out.append(
                CourseState(
                    cid, cid, title, unit, label, round(n_done / len(types), 2),
                    cid == current, levels,
                )
            )  # fmt: skip
        return out

    async def list_for_user(self, uid: str, conn: Any = None) -> list[CourseState]:
        return self._courses(uid)

    async def get_for_user(
        self, uid: str, course_id: int, conn: Any = None
    ) -> CourseState | None:
        return next((c for c in self._courses(uid) if c.id == course_id), None)

    # --- lesson_repository
    async def get_steps(self, course_id: int, pos: int) -> list[StepRow]:
        quiz = {
            "question": "Apa?",
            "options": [{"text": str(i), "correct": i == 0} for i in range(4)],
            "feedbackCorrect": "Benar!",
            "feedbackWrong": "Kurang tepat.",
        }
        return [
            StepRow(
                1, "READ", "MODE BACA", "Judul", "Ayo!", {"paragraphs": ["a", "b"]}
            ),
            StepRow(2, "QUIZ", "MODE KUIS", None, "Pilih jawabanmu!", quiz),
        ]

    # --- progress_repository
    async def get_stats(self, uid: str) -> StudyStats:
        today = self.minutes_today.get(uid, 0)
        streak = self.past_streak.get(uid, 0) + (1 if today >= 10 else 0)
        # Pretend today is Wednesday: Mon/Tue met, Wed depends on today's minutes.
        week = [DayRow(False, 12, True), DayRow(False, 12, True)]
        week.append(DayRow(True, today, today >= 10))
        week += [DayRow(False, 0, False)] * 4
        return StudyStats(streak=streak, week=week)

    async def record_completion(
        self, conn: Any, uid: str, course_id: int, pos: int, correct: bool, minutes: int
    ) -> None:
        self.recorded.append((course_id, pos, correct, minutes))
        self.complete(uid, course_id, pos)
        self.minutes_today[uid] = self.minutes_today.get(uid, 0) + minutes


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakeDB:
    db = FakeDB()
    db.users[BUDI_ID] = UserRow(
        BUDI_ID, "Budi Santoso", "budi@legaloo.id", BUDI_HASH, 10
    )
    db.complete(BUDI_ID, 2, 1)
    db.complete(BUDI_ID, 1, 1)
    db.complete(BUDI_ID, 1, 2)
    db.minutes_today[BUDI_ID] = 6
    db.past_streak[BUDI_ID] = 7

    for name in ("get_by_email", "get_by_id", "create"):
        monkeypatch.setattr(user_repository, name, getattr(db, name))
    for name in ("list_for_user", "get_for_user"):
        monkeypatch.setattr(course_repository, name, getattr(db, name))
    monkeypatch.setattr(lesson_repository, "get_steps", db.get_steps)
    monkeypatch.setattr(progress_repository, "get_stats", db.get_stats)
    monkeypatch.setattr(progress_repository, "record_completion", db.record_completion)

    @asynccontextmanager
    async def _tx():  # type: ignore[no-untyped-def]
        yield object()

    monkeypatch.setattr(session, "transaction", _tx)
    return db


@pytest.fixture
def token(client: TestClient, fake_db: FakeDB) -> str:
    r = client.post(
        "/auth/login", json={"email": "budi@legaloo.id", "password": "legaloo123"}
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
