from __future__ import annotations

from collections.abc import Mapping

import httpx
from sqlalchemy import text

from app.config import settings
from app.database import get_async_engine, get_redis
from app.services.ollama_service import test_ollama_connection


async def _probe_database() -> dict[str, object]:
    url = settings.database_url_or_none()
    if not url:
        return {"configured": False, "reachable": False, "message": "DATABASE_URL is not set"}

    try:
        async with get_async_engine().begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"configured": True, "reachable": True, "message": "Database connection is healthy"}
    except Exception as exc:
        return {"configured": True, "reachable": False, "message": str(exc)}


async def _probe_redis() -> dict[str, object]:
    try:
        redis = get_redis()
        await redis.ping()
        return {"configured": bool(settings.REDIS_URL), "reachable": True, "message": "Redis connection is healthy"}
    except Exception as exc:
        return {"configured": bool(settings.REDIS_URL), "reachable": False, "message": str(exc)}


async def _probe_ollama() -> dict[str, object]:
    try:
        connected = await test_ollama_connection()
        if not connected:
            return {"configured": bool(settings.OLLAMA_BASE_URL), "reachable": False, "message": "Ollama is not responding"}

        models: list[str] = []
        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=5) as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
            payload: Mapping[str, object] = response.json()
            raw_models = payload.get("models", [])
            if isinstance(raw_models, list):
                models = [str(item.get("name", "")) for item in raw_models if isinstance(item, dict) and item.get("name")]
        return {"configured": bool(settings.OLLAMA_BASE_URL), "reachable": True, "message": "Ollama is healthy", "models": models}
    except Exception as exc:
        return {"configured": bool(settings.OLLAMA_BASE_URL), "reachable": False, "message": str(exc)}


async def collect_system_status() -> dict[str, object]:
    database = await _probe_database()
    redis = await _probe_redis()
    ollama = await _probe_ollama()
    smtp_configured = bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)
    issues = [
        *settings.startup_issues(),
        *([f"Database: {database['message']}"] if not database.get("reachable") else []),
        *([f"Redis: {redis['message']}"] if not redis.get("reachable") else []),
        *([f"Ollama: {ollama['message']}"] if not ollama.get("reachable") else []),
        *([] if smtp_configured else ["SMTP_HOST and SMTP_FROM_EMAIL are not configured"]),
    ]
    return {
        "ok": not issues,
        "issues": issues,
        "database": database,
        "redis": redis,
        "ollama": ollama,
        "smtp": {"configured": smtp_configured},
    }
