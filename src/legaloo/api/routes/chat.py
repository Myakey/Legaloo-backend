from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...schemas.chat import ChatRequest
from ...services import chat_service

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        chat_service.answer(req), media_type="text/plain; charset=utf-8"
    )
