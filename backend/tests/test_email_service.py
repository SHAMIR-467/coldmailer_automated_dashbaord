import asyncio
from unittest.mock import MagicMock, patch

from app.services.email_service import check_daily_limit, is_bounce_error, send_email


def test_daily_limit_enforcement_via_redis_mock(mock_redis):
    mock_redis.get.return_value = "20000"
    sent, at_limit = check_daily_limit(mock_redis)
    assert sent == 20000
    assert at_limit is True


def test_sends_email_with_correct_headers(monkeypatch):
    monkeypatch.setattr("app.services.email_service.settings.SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr("app.services.email_service.settings.SMTP_PORT", 587)
    monkeypatch.setattr("app.services.email_service.settings.SMTP_FROM_EMAIL", "from@example.com")
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    with patch("smtplib.SMTP", return_value=smtp):
        assert asyncio.run(send_email("to@example.com", "Subject", "Body")) is True
    args = smtp.sendmail.call_args.args
    assert args[0] == "from@example.com"
    assert args[1] == ["to@example.com"]
    assert "Subject: Subject" in args[2]


def test_smtp_failure_returns_false(monkeypatch):
    monkeypatch.setattr("app.services.email_service.settings.SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr("app.services.email_service.settings.SMTP_FROM_EMAIL", "from@example.com")
    with patch("smtplib.SMTP", side_effect=RuntimeError("550 mailbox not found")):
        assert asyncio.run(send_email("to@example.com", "Subject", "Body")) is False


def test_bounce_detection_from_smtp_error_messages():
    assert is_bounce_error("550 mailbox not found")
    assert is_bounce_error("user unknown")
    assert not is_bounce_error("421 temporary rate limit")
