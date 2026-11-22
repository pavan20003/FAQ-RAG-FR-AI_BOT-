"""Environment-backed application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql://faqrag:faqrag@localhost:5432/faqrag"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int | None = None
    retrieval_vector_threshold: float = 0.3
    retrieval_keyword_threshold: float = 0.01
    retrieval_min_term_coverage: float = 0.25
    anthropic_api_key: str | None = None
    claude_model: str | None = None
    claude_max_tokens: int = 700
    claude_timeout_seconds: float = 30.0
    claude_max_retries: int = 2

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_ignore_empty=True, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Reuse one settings object so configuration stays consistent."""
    return Settings()
