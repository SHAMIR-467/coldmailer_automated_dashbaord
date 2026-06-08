from functools import lru_cache
from typing import Annotated
from urllib.parse import quote_plus, urlparse

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    PROXY_URL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM_NAME: str = ""
    SMTP_FROM_EMAIL: str = ""
    DAILY_EMAIL_LIMIT: int = 20000
    SCRAPE_BATCH_SIZE: int = 20
    SCRAPE_DELAY_MIN: float = 2.0
    SCRAPE_DELAY_MAX: float = 5.0
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def database_url(self) -> str:
        if self.SUPABASE_URL.startswith(("postgresql://", "postgresql+asyncpg://")):
            return self.SUPABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        parsed = urlparse(self.SUPABASE_URL)
        if not parsed.hostname:
            raise ValueError("SUPABASE_URL must be a Supabase project URL or a PostgreSQL URL")
        project_ref = parsed.hostname.split(".")[0]
        password = quote_plus(self.SUPABASE_KEY)
        return f"postgresql+asyncpg://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
