from fastapi import APIRouter
from pydantic import BaseModel
import httpx

from app.config import settings
from app.services.ollama_service import test_ollama_connection

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    supabase_url: str
    supabase_key: str
    redis_url: str
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


class SmtpTestRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    from_email: str = ""


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return SettingsResponse(
        supabase_url=settings.SUPABASE_URL,
        supabase_key="********" if settings.SUPABASE_KEY else "",
        redis_url=settings.REDIS_URL,
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
    )


@router.put("", response_model=dict[str, str])
async def update_settings() -> dict[str, str]:
    return {"status": "settings are read-only in this MVP"}


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
