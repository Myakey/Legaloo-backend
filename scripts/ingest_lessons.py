"""Demo chat corpus: embed every READ-step paragraph into `documents`.

Run locally, never on Vercel:

    uv run --group ingest python scripts/ingest_lessons.py

Each paragraph becomes one row with `source` = the level title. Re-running is
safe: rows whose source is a level title are deleted first, in the same
transaction as the inserts.
"""

import asyncio

from legaloo.core.config import get_settings
from legaloo.db.session import get_pool
from legaloo.repositories.lesson_repository import list_read_paragraphs
from legaloo.services.embedding_service import embed_document

_CONCURRENCY = 4


async def main() -> None:
    s = get_settings()
    if not s.database_url or not s.gemini_api_key:
        raise SystemExit("DATABASE_URL and GEMINI_API_KEY must be set (see .env)")

    paragraphs = await list_read_paragraphs()
    print(f"found {len(paragraphs)} READ paragraphs")

    sem = asyncio.Semaphore(_CONCURRENCY)

    async def embed_one(text: str) -> list[float]:
        async with sem:
            return await embed_document(text)

    embeddings = await asyncio.gather(*(embed_one(p) for _, p in paragraphs))
    sources = sorted({title for title, _ in paragraphs})

    async with (await get_pool()).acquire() as conn, conn.transaction():
        deleted = await conn.execute(
            "delete from documents where source = any($1::text[])", sources
        )
        await conn.executemany(
            "insert into documents (content, source, embedding) values ($1, $2, $3::vector)",
            [
                (text, title, "[" + ",".join(map(str, emb)) + "]")
                for (title, text), emb in zip(paragraphs, embeddings, strict=True)
            ],
        )
    print(f"{deleted.removeprefix('DELETE ')} old rows removed")
    print(f"inserted {len(paragraphs)} rows from {len(sources)} levels")


if __name__ == "__main__":
    asyncio.run(main())
