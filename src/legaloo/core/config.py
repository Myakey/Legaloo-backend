from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres (Supabase) connection string, pgvector enabled.
    database_url: str = ""

    # Embeddings + generation.
    gemini_api_key: str = ""
    embedding_model: str = "gemini-embedding-001"
    llm_model: str = "gemini-2.5-flash"

    # Retrieval behaviour.
    top_k: int = 5
    max_context_chars: int = 6000

    # Auth (HS256 JWT). Must be set in every environment; tokens can't be issued without it.
    jwt_secret: str = ""
    jwt_expire_days: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
