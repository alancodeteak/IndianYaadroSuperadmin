import smtplib
import asyncio

import pytest

from app.api.core.config import get_settings
from app.api.exceptions.http_errors import ApiError
from app.infrastructure.otp_notifier import SMTPOTPNotifier


class _SMTPClientStub:
    def __init__(self, host: str, port: int, timeout: int):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in = False
        self.sent = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username: str, password: str):
        self.logged_in = bool(username and password)

    def send_message(self, msg):
        self.sent = True


def _smtp_settings():
    settings = get_settings()
    settings.SMTP_ENABLED = True
    settings.SMTP_HOST = "smtp.test.local"
    settings.SMTP_PORT = 587
    settings.SMTP_USERNAME = "mailer@test.local"
    settings.SMTP_PASSWORD = "secret"
    settings.SMTP_USE_TLS = True
    settings.SMTP_USE_SSL = False
    settings.SMTP_FROM_EMAIL = "mailer@test.local"
    settings.SMTP_FROM_NAME = "Test Mailer"
    return settings


def test_smtp_notifier_send_success(monkeypatch):
    settings = _smtp_settings()

    stub = _SMTPClientStub(settings.SMTP_HOST, settings.SMTP_PORT, 10)

    def _factory(host: str, port: int, timeout: int):
        assert host == settings.SMTP_HOST
        assert port == settings.SMTP_PORT
        return stub

    monkeypatch.setattr(smtplib, "SMTP", _factory)
    notifier = SMTPOTPNotifier(settings=settings)
    asyncio.run(notifier.send_otp("admin", "admin@test.com", "123456", 300))

    assert stub.started_tls is True
    assert stub.logged_in is True
    assert stub.sent is True


def test_smtp_notifier_send_failure_maps_api_error(monkeypatch):
    settings = _smtp_settings()

    class _FailingClient(_SMTPClientStub):
        def send_message(self, msg):
            raise RuntimeError("smtp down")

    def _factory(host: str, port: int, timeout: int):
        return _FailingClient(host, port, timeout)

    monkeypatch.setattr(smtplib, "SMTP", _factory)
    notifier = SMTPOTPNotifier(settings=settings)

    with pytest.raises(ApiError) as exc:
        asyncio.run(notifier.send_otp("portal", "portal@test.com", "654321", 300))

    assert exc.value.code == "OTP_DELIVERY_FAILED"
