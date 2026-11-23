"""pgvector similarity search over the `documents` table."""

from ..core.config import get_settings
from ..db.session import get_pool
from ..schemas.document import Chunk

_SEARCH_SQL = """
SELECT id::text, content, source, 1 - (embedding <=> $1::vector) AS score
FROM documents
ORDER BY embedding <=> $1::vector
LIMIT $2
"""


async def search_similar(
    embedding: list[float], limit: int | None = None
) -> list[Chunk]:
    top_k = limit if limit is not None else get_settings().top_k
    vec = "[" + ",".join(str(x) for x in embedding) + "]"
    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(_SEARCH_SQL, vec, top_k)
    return [Chunk(**dict(r)) for r in rows]
