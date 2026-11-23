"""RAG chat orchestration: embed -> retrieve -> build prompt -> stream answer.

The stream must never be empty and must not die with a traceback mid-response:
once the 200 is sent the client can't see an error status, so failures are
turned into a short Indonesian message in the stream itself.
"""

import logging
from collections.abc import AsyncIterator

from ..repositories import document_repository
from ..schemas.chat import ChatRequest
from ..schemas.document import Chunk
from . import embedding_service, llm_service
from .prompt_service import build_prompt

log = logging.getLogger(__name__)

GENERAL_NOTE_TEXT = (
    "Catatan: Legaloo belum punya sumber hukum untuk pertanyaan ini, "
    "jadi ini informasi umum ya.\n\n"
)
GENERAL_NOTE_VOICE = "Ini informasi umum ya. "
FALLBACK_ANSWER = (
    "Maaf, Legaloo belum bisa menjawab sekarang. Coba lagi sebentar lagi ya."
)


async def _retrieve(query: str) -> list[Chunk]:
    # Retrieval failing (DB down, embedding error) degrades to a general answer.
    try:
        embedding = await embedding_service.embed_query(query)
        return await document_repository.search_similar(embedding)
    except Exception:
        log.exception("retrieval failed; answering without context")
        return []


async def answer(req: ChatRequest) -> AsyncIterator[str]:
    chunks = await _retrieve(req.query)
    prompt = build_prompt(req.query, chunks, req.voice_mode)

    if not chunks:
        yield GENERAL_NOTE_VOICE if req.voice_mode else GENERAL_NOTE_TEXT

    produced = False
    try:
        async for piece in llm_service.stream_completion(prompt):
            if piece:
                produced = True
                yield piece
    except Exception:
        log.exception("generation failed")
    if not produced:
        yield FALLBACK_ANSWER
