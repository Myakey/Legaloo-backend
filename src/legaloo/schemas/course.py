from typing import Any, Literal

from pydantic import Field

from .base import CamelModel

LevelType = Literal["LESSON", "PRACTICE"]
LevelStateName = Literal["COMPLETED", "ACTIVE", "LOCKED"]


class LevelNode(CamelModel):
    id: int
    type: LevelType
    state: LevelStateName
    title: str


class Course(CamelModel):
    id: int
    number: int
    title: str
    progress: float
    unit_label: str
    is_current: bool
    levels: list[LevelNode]


class DayStatus(CamelModel):
    label: str
    completed: bool


class UserProgress(CamelModel):
    user_name: str
    streak_count: int
    minutes_studied: int
    daily_goal_minutes: int
    week: list[DayStatus]
    current_course_id: int
    current_unit_number: int


class LessonStep(CamelModel):
    position: int
    kind: Literal["READ", "EXAMPLES", "QUIZ"]
    mode_label: str
    title: str | None
    mascot_message: str | None
    # Passed through unchanged from the jsonb column; its keys are already camelCase.
    content: dict[str, Any]


class Lesson(CamelModel):
    course_id: int
    level_id: int
    type: LevelType
    title: str
    steps: list[LessonStep]


class CompleteRequest(CamelModel):
    correct: bool = True
    # Clamped to 0..60 in the service rather than rejected.
    minutes_spent: int = Field(default=0)


class CompleteResponse(CamelModel):
    course: Course
    progress: UserProgress
