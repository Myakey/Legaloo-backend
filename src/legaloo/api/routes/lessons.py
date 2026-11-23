from fastapi import APIRouter

from ...schemas.course import CompleteRequest, CompleteResponse, Lesson
from ...services import lesson_service
from ..deps import CurrentUser

router = APIRouter(tags=["lessons"])


@router.get("/courses/{course_id}/levels/{level_id}/lesson")
async def get_lesson(course_id: int, level_id: int, user: CurrentUser) -> Lesson:
    return await lesson_service.get_lesson(user, course_id, level_id)


@router.post("/courses/{course_id}/levels/{level_id}/complete")
async def complete_level(
    course_id: int, level_id: int, req: CompleteRequest, user: CurrentUser
) -> CompleteResponse:
    return await lesson_service.complete_level(user, course_id, level_id, req)
