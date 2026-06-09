from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


RUNTIME_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "data" / "runtime_settings.json"


def _default_database_url() -> str:
    db_path = Path(__file__).resolve().parents[1] / "data" / "leadgen.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


def _normalize_sqlite_url(url: str) -> str:
    if not url.startswith(("sqlite+aiosqlite:///", "sqlite:///")):
        raise ValueError("DATABASE_URL must use SQLite, for example sqlite+aiosqlite:///path/to/leadgen.db")

    prefix = "sqlite+aiosqlite:///" if url.startswith("sqlite+aiosqlite:///") else "sqlite:///"
    raw_path = url.split("///", 1)[1].strip()
    if not raw_path:
        raise ValueError("DATABASE_URL must point to a SQLite file")

    path = Path(raw_path)
    if not path.is_absolute():
        path = (Path(__file__).resolve().parents[2] / path).resolve()
    return f"{prefix}{path.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = Field(default_factory=_default_database_url)
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
        return _normalize_sqlite_url(self.DATABASE_URL)

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)

    def database_url_or_none(self) -> str | None:
        try:
            return self.database_url
        except ValueError:
            return None

    def startup_issues(self) -> list[str]:
        issues: list[str] = []
        if not self.database_url_or_none():
            issues.append("DATABASE_URL must be set")
        if not self.REDIS_URL:
            issues.append("REDIS_URL must be set")
        if not self.OLLAMA_BASE_URL:
            issues.append("OLLAMA_BASE_URL must be set")
        return issues


def load_runtime_settings() -> dict[str, Any]:
    if not RUNTIME_SETTINGS_PATH.exists():
        return {}
    try:
        data = json.loads(RUNTIME_SETTINGS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_runtime_settings(overrides: dict[str, Any]) -> None:
    RUNTIME_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_SETTINGS_PATH.write_text(json.dumps(overrides, indent=2, sort_keys=True), encoding="utf-8")


def apply_runtime_settings(overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        field_name = key.upper() if hasattr(settings, key.upper()) else key
        if hasattr(settings, field_name):
            if field_name == "DATABASE_URL":
                value = _normalize_sqlite_url(str(value))
            if field_name == "CORS_ORIGINS" and isinstance(value, str):
                value = [origin.strip() for origin in value.split(",") if origin.strip()]
            setattr(settings, field_name, value)
    from app.database import reset_database_resources

    reset_database_resources()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
apply_runtime_settings(load_runtime_settings())
