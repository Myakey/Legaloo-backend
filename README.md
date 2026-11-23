# Legaloo — backend

FastAPI RAG service. Retrieval and prompt assembly happen here; the LLM is remote.

## Run locally

    uv sync
    cp .env.example .env     # fill in DATABASE_URL and GEMINI_API_KEY
    uv run uvicorn legaloo.main:app --reload

Docs at http://127.0.0.1:8000/docs

## Ingestion

Ingestion deps are in a separate group so they never reach the serverless bundle:

    uv run --group ingest python scripts/ingest.py ./corpus

## Deploy

    vercel

`api/index.py` is the entrypoint Vercel loads; it imports the app from `src/legaloo`.
Region is pinned to `sin1` (Singapore) in `vercel.json`.

## Layout

    api/index.py                    Vercel shim
    src/legaloo/
      main.py                       FastAPI app; registers all routers
      api/routes/                   route handlers (health, chat)
      core/                         settings, shared HTTP client
      db/session.py                 asyncpg connection pool
      schemas/                      Pydantic request/response models
      repositories/                 database queries (pgvector search)
      services/                     business logic (embedding, prompt, LLM, chat)
    scripts/ingest.py               offline, not deployed
