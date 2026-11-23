"""Playing and completing levels. Lock rules come from the course-state query."""

from ..core.errors import (
    MSG_COURSE_NOT_FOUND,
    MSG_LEVEL_LOCKED,
    MSG_LEVEL_NOT_FOUND,
    AppError,
)
from ..db import session
from ..repositories import course_repository, lesson_repository, progress_repository
from ..repositories.course_repository import CourseState, LevelState
from ..repositories.user_repository import UserRow
from ..schemas.course import CompleteRequest, CompleteResponse, Lesson, LessonStep
from . import course_service

MAX_MINUTES_PER_COMPLETION = 60


def _playable_level(course: CourseState | None, level_id: int) -> LevelState:
    if course is None:
        raise AppError(404, MSG_COURSE_NOT_FOUND)
    level = next((lv for lv in course.levels if lv.id == level_id), None)
    if level is None:
        raise AppError(404, MSG_LEVEL_NOT_FOUND)
    if level.state == "LOCKED":
        raise AppError(403, MSG_LEVEL_LOCKED)
    return level  # ACTIVE, or COMPLETED (replay is allowed)


async def get_lesson(user: UserRow, course_id: int, level_id: int) -> Lesson:
    course = await course_repository.get_for_user(user.id, course_id)
    level = _playable_level(course, level_id)
    steps = await lesson_repository.get_steps(course_id, level_id)
    return Lesson(
        course_id=course_id,
        level_id=level_id,
        type=level.type,
        title=level.title,
        steps=[
            LessonStep(
                position=s.position,
                kind=s.kind,
                mode_label=s.mode_label,
                title=s.title,
                mascot_message=s.mascot_message,
                content=s.content,
            )
            for s in steps
        ],
    )


async def complete_level(
    user: UserRow, course_id: int, level_id: int, req: CompleteRequest
) -> CompleteResponse:
    minutes = max(0, min(MAX_MINUTES_PER_COMPLETION, req.minutes_spent))
    async with session.transaction() as conn:
        course = await course_repository.get_for_user(user.id, course_id, conn)
        _playable_level(course, level_id)
        await progress_repository.record_completion(
            conn, user.id, course_id, level_id, req.correct, minutes
        )
    updated = await course_service.get_course(user, course_id)
    progress = await course_service.get_progress(user)
    return CompleteResponse(course=updated, progress=progress)
