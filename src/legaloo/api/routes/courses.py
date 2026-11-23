from fastapi import APIRouter

from ...schemas.course import Course, UserProgress
from ...services import course_service
from ..deps import CurrentUser

router = APIRouter(tags=["courses"])


@router.get("/courses")
async def list_courses(user: CurrentUser) -> list[Course]:
    return await course_service.list_courses(user)


@router.get("/courses/{course_id}")
async def get_course(course_id: int, user: CurrentUser) -> Course:
    return await course_service.get_course(user, course_id)


@router.get("/me/progress")
async def get_progress(user: CurrentUser) -> UserProgress:
    return await course_service.get_progress(user)
