"""Embeddings over HTTP. No local model — keeps the bundle small.

Queries and documents must use the same model and dimension as the
`documents.embedding vector(768)` column, so both go through `embed()`.
"""

from typing import Literal

from ..core.config import get_settings
from ..core.http import client

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

# Must match `vector(768)` in db/schema.sql. gemini-embedding-001 returns 3072
# dims unless told otherwise. Reduced-dim vectors are not unit-normalized, which
# is fine for cosine (`<=>`) but not for inner product (`<#>`).
EMBEDDING_DIM = 768

TaskType = Literal["RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT"]


async def embed(text: str, task_type: TaskType) -> list[float]:
    s = get_settings()
    resp = await client().post(
        f"{_ENDPOINT}/{s.embedding_model}:embedContent",
        headers={"x-goog-api-key": s.gemini_api_key},
        json={
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
            "outputDimensionality": EMBEDDING_DIM,
        },
    )
    resp.raise_for_status()
    values = resp.json()["embedding"]["values"]
    if len(values) != EMBEDDING_DIM:
        raise ValueError(f"expected {EMBEDDING_DIM}-dim embedding, got {len(values)}")
    return values


async def embed_query(text: str) -> list[float]:
    return await embed(text, "RETRIEVAL_QUERY")


async def embed_document(text: str) -> list[float]:
    return await embed(text, "RETRIEVAL_DOCUMENT")
