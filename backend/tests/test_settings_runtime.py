from fastapi.testclient import TestClient

from app import config
from app.main import app


def test_settings_update_persists_runtime_file(tmp_path, monkeypatch):
    runtime_file = tmp_path / "runtime_settings.json"
    monkeypatch.setattr(config, "RUNTIME_SETTINGS_PATH", runtime_file)
    original_settings = config.settings.model_dump()

    payload = {
        "database_url": "sqlite+aiosqlite:///backend/data/test-runtime.db",
        "redis_url": "redis://localhost:6379/0",
        "proxy_url": "",
        "smtp_pass": "secret",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "user",
        "smtp_from_name": "Sender",
        "smtp_from_email": "sender@example.com",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3",
        "daily_email_limit": 100,
        "scrape_batch_size": 10,
        "scrape_delay_min": 1.0,
        "scrape_delay_max": 2.0,
        "cors_origins": ["http://localhost:5173"],
    }

    client = TestClient(app)
    try:
        response = client.put("/api/settings", json=payload)
    finally:
        config.apply_runtime_settings(original_settings)

    assert response.status_code == 200
    assert runtime_file.exists()
    saved = config.load_runtime_settings()
    assert saved["database_url"] == payload["database_url"]
    assert saved["smtp_host"] == payload["smtp_host"]


def test_dashboard_stats_survives_redis_failure(monkeypatch):
    def raise_redis_error():
        raise RuntimeError("redis down")

    monkeypatch.setattr("app.routers.dashboard.get_redis", raise_redis_error)
    client = TestClient(app)

    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    assert response.json()["emails_sent_today"] == 0
