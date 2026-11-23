"""Courses and home-screen progress, shaped for the app's Models.kt."""

from ..core.errors import MSG_COURSE_NOT_FOUND, AppError
from ..repositories import course_repository, progress_repository
from ..repositories.course_repository import CourseState
from ..repositories.user_repository import UserRow
from ..schemas.course import Course, DayStatus, LevelNode, UserProgress

# Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu.
WEEK_LABELS = ["S", "S", "R", "K", "J", "S", "M"]


def to_course(c: CourseState) -> Course:
    return Course(
        id=c.id,
        number=c.number,
        title=c.title,
        progress=c.progress,
        unit_label=c.unit_label,
        is_current=c.is_current,
        levels=[
            LevelNode(id=lv.id, type=lv.type, state=lv.state, title=lv.title)
            for lv in c.levels
        ],
    )


async def list_courses(user: UserRow) -> list[Course]:
    return [to_course(c) for c in await course_repository.list_for_user(user.id)]


async def get_course_state(user: UserRow, course_id: int) -> CourseState:
    course = await course_repository.get_for_user(user.id, course_id)
    if course is None:
        raise AppError(404, MSG_COURSE_NOT_FOUND)
    return course


async def get_course(user: UserRow, course_id: int) -> Course:
    return to_course(await get_course_state(user, course_id))


async def get_progress(user: UserRow) -> UserProgress:
    stats = await progress_repository.get_stats(user.id)
    courses = await course_repository.list_for_user(user.id)
    current = next(
        (c for c in courses if c.is_current), courses[0] if courses else None
    )
    return UserProgress(
        user_name=user.name,
        streak_count=stats.streak,
        minutes_studied=stats.minutes_today,
        daily_goal_minutes=user.daily_goal_minutes,
        week=[
            DayStatus(label=label, completed=day.completed)
            for label, day in zip(WEEK_LABELS, stats.week, strict=True)
        ],
        current_course_id=current.id if current else 1,
        current_unit_number=current.unit_number if current else 1,
    )
