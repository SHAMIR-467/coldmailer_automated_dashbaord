from app.config import settings


def test_startup_issues_reports_missing_database_url(monkeypatch):
    monkeypatch.setattr("app.config.settings.DATABASE_URL", "")

    issues = settings.startup_issues()

    assert any("DATABASE_URL" in issue for issue in issues)
