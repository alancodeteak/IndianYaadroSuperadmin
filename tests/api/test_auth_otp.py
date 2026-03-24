from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.api.core.config import get_settings
from app.api.deps import get_auth_service, get_session_service
from app.main import app
from app.services.auth_service import AuthService
from app.services.otp_service import InMemoryOTPStore


@dataclass
class _NotifierStub:
    last_otp: str | None = None

    async def send_otp(
        self, purpose: str, target: str, otp_code: str, expires_in_seconds: int
    ) -> None:
        self.last_otp = otp_code


def _build_auth_service(admin_email: str, portal_email: str) -> tuple[AuthService, _NotifierStub]:
    settings = get_settings()
    settings.ADMIN_OTP_EMAILS = admin_email
    settings.PORTAL_OTP_EMAILS = portal_email
    settings.OTP_RESEND_COOLDOWN_SECONDS = 0
    notifier = _NotifierStub()
    service = AuthService(
        settings=settings,
        otp_store=InMemoryOTPStore(),
        otp_notifier=notifier,
        session_service=get_session_service(),
    )
    return service, notifier


def test_admin_otp_login_and_logout_flow():
    service, notifier = _build_auth_service("admin@test.com", "portal@test.com")
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    send_resp = client.post("/auth/send-otp", json={"email": "admin@test.com"})
    assert send_resp.status_code == 200
    assert send_resp.json()["data"]["code"] == "OTP_SENT"

    verify_resp = client.post(
        "/auth/verify-otp",
        json={"email": "admin@test.com", "otp_code": notifier.last_otp},
    )
    assert verify_resp.status_code == 200
    token = verify_resp.json()["data"]["access_token"]
    assert verify_resp.json()["data"]["role"] == "SUPERADMIN"

    logout_resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    post_logout = client.get("/portal/", headers={"Authorization": f"Bearer {token}"})
    assert post_logout.status_code == 401
    assert post_logout.json()["error"]["code"] == "AUTH_SESSION_EXPIRED"
    app.dependency_overrides.clear()


def test_portal_otp_login_success():
    service, notifier = _build_auth_service("admin@test.com", "portal@test.com")
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    send_resp = client.post("/portal/send-otp", json={"email": "portal@test.com"})
    assert send_resp.status_code == 200
    assert send_resp.json()["data"]["code"] == "OTP_SENT"

    verify_resp = client.post(
        "/portal/verify-otp",
        json={"email": "portal@test.com", "otp_code": notifier.last_otp},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["data"]["role"] == "PORTAL_USER"
    app.dependency_overrides.clear()


def test_scoped_login_endpoints_work_for_admin():
    service, notifier = _build_auth_service("admin@test.com", "portal@test.com")
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    send_resp = client.post(
        "/login/send-otp",
        json={"scope": "admin", "email": "admin@test.com"},
    )
    assert send_resp.status_code == 200
    assert send_resp.json()["data"]["code"] == "OTP_SENT"

    verify_resp = client.post(
        "/login/verify-otp",
        json={"scope": "admin", "email": "admin@test.com", "otp_code": notifier.last_otp},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["data"]["role"] == "SUPERADMIN"
    app.dependency_overrides.clear()


def test_send_otp_rejects_email_not_in_allowlist():
    service, _ = _build_auth_service("admin@test.com", "portal@test.com")
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    send_resp = client.post(
        "/login/send-otp",
        json={"scope": "admin", "email": "not-allowed@test.com"},
    )
    assert send_resp.status_code == 403
    assert send_resp.json()["error"]["code"] == "UNAUTHORIZED"
    app.dependency_overrides.clear()

