from dataclasses import dataclass
import asyncio

from app.api.core.config import get_settings
from app.api.exceptions.http_errors import ApiError
from app.services.auth_service import AuthService
from app.services.otp_service import InMemoryOTPStore
from app.services.session_service import SessionService


@dataclass
class _NotifierStub:
    last_otp: str | None = None

    async def send_otp(self, purpose: str, target: str, otp_code: str, expires_in_seconds: int) -> None:
        self.last_otp = otp_code


def _build_service() -> tuple[AuthService, _NotifierStub]:
    settings = get_settings()
    settings.ADMIN_OTP_EMAILS = "admin@test.com"
    settings.PORTAL_OTP_EMAILS = "portal@test.com"
    settings.OTP_TTL_SECONDS = 300
    settings.OTP_MAX_ATTEMPTS = 2
    settings.OTP_RESEND_COOLDOWN_SECONDS = 0
    notifier = _NotifierStub()
    service = AuthService(
        settings=settings,
        otp_store=InMemoryOTPStore(),
        otp_notifier=notifier,
        session_service=SessionService(),
    )
    return service, notifier


def test_admin_otp_verify_success_issues_bearer_session():
    service, notifier = _build_service()
    asyncio.run(service.send_admin_otp("admin@test.com"))
    session = service.verify_admin_otp("admin@test.com", notifier.last_otp or "")
    assert session.token_type == "bearer"
    assert session.role.value == "SUPERADMIN"


def test_admin_otp_invalid_attempts_exceeded():
    service, notifier = _build_service()
    asyncio.run(service.send_admin_otp("admin@test.com"))
    assert notifier.last_otp

    for _ in range(2):
        try:
            service.verify_admin_otp("admin@test.com", "000000")
            assert False, "Expected OTP_INVALID"
        except ApiError as exc:
            assert exc.code in {"OTP_INVALID", "OTP_ATTEMPTS_EXCEEDED"}

    try:
        service.verify_admin_otp("admin@test.com", "000000")
        assert False, "Expected OTP_ATTEMPTS_EXCEEDED"
    except ApiError as exc:
        assert exc.code == "OTP_ATTEMPTS_EXCEEDED"

