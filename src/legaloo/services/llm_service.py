"""Streaming generation. Yields text chunks so the client can start TTS early."""

import json
from collections.abc import AsyncIterator

from ..core.config import get_settings
from ..core.http import client

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"


async def stream_completion(prompt: str) -> AsyncIterator[str]:
    s = get_settings()
    url = f"{_ENDPOINT}/{s.llm_model}:streamGenerateContent?alt=sse"

    async with client().stream(
        "POST",
        url,
        headers={"x-goog-api-key": s.gemini_api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
    ) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            payload = line.removeprefix("data: ").strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                data = json.loads(payload)
                yield data["candidates"][0]["content"]["parts"][0]["text"]
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
