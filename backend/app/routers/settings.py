from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
import httpx

from app.config import apply_runtime_settings, save_runtime_settings, settings
from app.database import ensure_database_schema
from app.services.ollama_service import test_ollama_connection
from app.services.system_status import collect_system_status

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    database_url: str
    redis_url: str
    proxy_url: str
    smtp_pass: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from_name: str
    smtp_from_email: str
    ollama_base_url: str
    ollama_model: str
    daily_email_limit: int
    scrape_batch_size: int
    scrape_delay_min: float
    scrape_delay_max: float
    cors_origins: list[str]


class SettingsUpdateRequest(BaseModel):
    database_url: str = Field(min_length=1)
    redis_url: str = Field(min_length=1)
    proxy_url: str = ""
    smtp_pass: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_from_name: str = ""
    smtp_from_email: str = ""
    ollama_base_url: str = ""
    ollama_model: str = "llama3"
    daily_email_limit: int = Field(default=20000, ge=1)
    scrape_batch_size: int = Field(default=20, ge=1, le=500)
    scrape_delay_min: float = Field(default=2.0, ge=0)
    scrape_delay_max: float = Field(default=5.0, ge=0)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("sqlite+aiosqlite:///", "sqlite:///")):
            raise ValueError("DATABASE_URL must use SQLite, for example sqlite+aiosqlite:///backend/data/leadgen.db")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


class SmtpTestRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    from_email: str = ""


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return SettingsResponse(
        database_url=settings.database_url,
        redis_url=settings.REDIS_URL,
        proxy_url=settings.PROXY_URL,
        smtp_pass="********" if settings.SMTP_PASS else "",
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_USER,
        smtp_from_name=settings.SMTP_FROM_NAME,
        smtp_from_email=settings.SMTP_FROM_EMAIL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        ollama_model=settings.OLLAMA_MODEL,
        daily_email_limit=settings.DAILY_EMAIL_LIMIT,
        scrape_batch_size=settings.SCRAPE_BATCH_SIZE,
        scrape_delay_min=settings.SCRAPE_DELAY_MIN,
        scrape_delay_max=settings.SCRAPE_DELAY_MAX,
        cors_origins=settings.CORS_ORIGINS,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(payload: SettingsUpdateRequest) -> SettingsResponse:
    runtime_settings = payload.model_dump()
    save_runtime_settings(runtime_settings)
    apply_runtime_settings(runtime_settings)
    try:
        await ensure_database_schema()
    except Exception:
        pass
    return await get_settings()


@router.post("/test-smtp", response_model=dict[str, bool | str])
async def test_smtp() -> dict[str, bool | str]:
    configured = bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)
    return {"ok": configured, "message": "SMTP settings present" if configured else "SMTP_HOST and SMTP_FROM_EMAIL are required"}


@router.put("/test-smtp", response_model=dict[str, bool | str | None])
async def test_smtp_credentials(payload: SmtpTestRequest) -> dict[str, bool | str | None]:
    import smtplib

    try:
        if payload.smtp_port == 465:
            smtp = smtplib.SMTP_SSL(payload.smtp_host, payload.smtp_port, timeout=10)
        else:
            smtp = smtplib.SMTP(payload.smtp_host, payload.smtp_port, timeout=10)
        with smtp:
            if payload.smtp_port != 465:
                smtp.starttls()
            if payload.smtp_user:
                smtp.login(payload.smtp_user, payload.smtp_pass)
        return {"success": True, "error": None}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.post("/test-ollama", response_model=dict[str, bool])
async def test_ollama() -> dict[str, bool]:
    return {"ok": await test_ollama_connection()}


@router.get("/test-ollama", response_model=dict[str, object])
async def get_test_ollama() -> dict[str, object]:
    connected = await test_ollama_connection()
    models: list[str] = []
    if connected:
        try:
            async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=5) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                models = [item.get("name", "") for item in response.json().get("models", []) if item.get("name")]
        except Exception:
            models = []
    return {"connected": connected, "models": models}


@router.get("/status", response_model=dict[str, object])
async def get_system_status() -> dict[str, object]:
    return await collect_system_status()
