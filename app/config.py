"""Environment-backed application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql://faqrag:faqrag@localhost:5432/faqrag"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int | None = None
    retrieval_vector_threshold: float = 0.5
    retrieval_keyword_threshold: float = 0.1
    retrieval_min_term_coverage: float = 0.65
    anthropic_api_key: str | None = None
    claude_model: str | None = None
    claude_max_tokens: int = 700
    claude_timeout_seconds: float = 30.0
    claude_max_retries: int = 2
    admin_token: str | None = None
    cors_allow_origins: str = ""
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    max_request_bytes: int = 65536
    support_email: str | None = None
    outbox_path: str = "data/outbox/messages.jsonl"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_address: str | None = None
    smtp_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_ignore_empty=True, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Reuse one settings object so configuration stays consistent."""
    return Settings()
