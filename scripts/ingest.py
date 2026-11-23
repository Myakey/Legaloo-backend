"""Offline ingestion. Run locally — never on the request path.

uv run --group ingest python scripts/ingest.py ./corpus
"""

import asyncio
import sys
from pathlib import Path


async def main(corpus_dir: str) -> None:
    paths = sorted(Path(corpus_dir).rglob("*.pdf"))
    print(f"found {len(paths)} documents in {corpus_dir}")
    # TODO: extract -> chunk -> embed (RETRIEVAL_DOCUMENT) -> upsert into pgvector
    raise SystemExit("ingestion not implemented yet")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "./corpus"))
