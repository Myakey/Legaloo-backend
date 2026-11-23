"""Chat with Gemini and pgvector mocked."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from legaloo.repositories import document_repository
from legaloo.schemas.document import Chunk
from legaloo.services import chat_service, embedding_service, llm_service

CHUNK = Chunk(id="1", content="Penumpang wajib memakai helm.", source="Helm", score=0.9)


@pytest.fixture
def gemini(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    state: dict[str, Any] = {
        "chunks": [CHUNK],
        "pieces": ["Ya, ", "wajib."],
        "prompt": None,
    }

    async def embed_query(text: str) -> list[float]:
        return [0.0] * embedding_service.EMBEDDING_DIM

    async def search_similar(embedding: list[float], limit: int | None = None):
        return state["chunks"]

    async def stream_completion(prompt: str) -> AsyncIterator[str]:
        state["prompt"] = prompt
        for p in state["pieces"]:
            if isinstance(p, Exception):
                raise p
            yield p

    monkeypatch.setattr(embedding_service, "embed_query", embed_query)
    monkeypatch.setattr(document_repository, "search_similar", search_similar)
    monkeypatch.setattr(llm_service, "stream_completion", stream_completion)
    return state


def _ask(client: TestClient, voice: bool = False) -> str:
    r = client.post(
        "/chat",
        json={"query": "Apakah penumpang motor wajib pakai helm?", "voice_mode": voice},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    return r.text


def test_chat_with_context(client: TestClient, gemini: dict[str, Any]) -> None:
    assert _ask(client) == "Ya, wajib."
    assert "[Helm]" in gemini["prompt"]


def test_chat_without_context_still_answers(
    client: TestClient, gemini: dict[str, Any]
) -> None:
    gemini["chunks"] = []
    assert _ask(client) == chat_service.GENERAL_NOTE_TEXT + "Ya, wajib."
    assert "tidak tahu" not in gemini["prompt"]
    assert _ask(client, voice=True).startswith(chat_service.GENERAL_NOTE_VOICE)


def test_chat_retrieval_failure_degrades(
    client: TestClient, gemini: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def broken(text: str) -> list[float]:
        raise RuntimeError("gemini down")

    monkeypatch.setattr(embedding_service, "embed_query", broken)
    assert _ask(client) == chat_service.GENERAL_NOTE_TEXT + "Ya, wajib."


@pytest.mark.parametrize("pieces", [[], [""], [RuntimeError("boom")]])
def test_chat_never_streams_empty(
    client: TestClient, gemini: dict[str, Any], pieces: list
) -> None:
    gemini["pieces"] = pieces
    assert _ask(client) == chat_service.FALLBACK_ANSWER


def test_chat_keeps_partial_answer_on_midstream_error(
    client: TestClient, gemini: dict[str, Any]
) -> None:
    gemini["pieces"] = ["Ya, ", RuntimeError("boom")]
    assert _ask(client) == "Ya, "


async def test_embed_sends_768_dims(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None: ...

        def json(self) -> dict:
            return {"embedding": {"values": [0.1] * 768}}

    class FakeClient:
        async def post(self, url: str, **kwargs: Any) -> FakeResponse:
            sent.update(url=url, **kwargs)
            return FakeResponse()

    monkeypatch.setattr(embedding_service, "client", lambda: FakeClient())
    for fn, task in (
        (embedding_service.embed_query, "RETRIEVAL_QUERY"),
        (embedding_service.embed_document, "RETRIEVAL_DOCUMENT"),
    ):
        assert len(await fn("helm")) == 768
        assert sent["json"]["outputDimensionality"] == 768
        assert sent["json"]["taskType"] == task
