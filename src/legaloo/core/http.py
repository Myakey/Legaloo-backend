"""Module-level HTTP client.

Fluid compute reuses function instances across invocations, so building the
client once at import time avoids re-establishing TLS on every request.
"""

import httpx

_client: httpx.AsyncClient | None = None


def client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))
    return _client
