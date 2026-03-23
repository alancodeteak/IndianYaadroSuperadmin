from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from secrets import randbelow

from starlette import status

from app.api.core.config import Settings
from app.api.core.logger import get_logger
from app.api.core.security import decode_token, generate_access_token
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.domain.enums.roles import Role
from app.services.otp_service import (
    OTPChallenge,
    OTPNotifier,
    OTPStore,
    expiry_from_now,
    hash_otp,
    utc_now,
)
from app.services.session_service import SessionService

log = get_logger(__name__)


@dataclass
class AuthSession:
    access_token: str
    token_type: str
    expires_at: datetime
    role: Role


class AuthService:
    def __init__(
        self,
        settings: Settings,
        otp_store: OTPStore,
        otp_notifier: OTPNotifier,
        session_service: SessionService,
    ) -> None:
        self.settings = settings
        self.otp_store = otp_store
        self.otp_notifier = otp_notifier
        self.session_service = session_service

    def send_admin_otp(self, email: str) -> None:
        self._send_otp(purpose="admin", role=Role.SUPERADMIN, email=email)

    def send_portal_otp(self, email: str) -> None:
        self._send_otp(purpose="portal", role=Role.PORTAL_USER, email=email)

    def verify_admin_otp(self, email: str, otp_code: str) -> AuthSession:
        return self._verify_otp(purpose="admin", role=Role.SUPERADMIN, email=email, otp_code=otp_code)

    def verify_portal_otp(self, email: str, otp_code: str) -> AuthSession:
        return self._verify_otp(
            purpose="portal", role=Role.PORTAL_USER, email=email, otp_code=otp_code
        )

    def logout(self, access_token: str) -> None:
        payload = decode_token(access_token)
        jti = str(payload.get("jti") or "")
        exp = int(payload.get("exp") or 0)
        if jti and exp:
            self.session_service.revoke_jti(jti=jti, exp_timestamp=exp)

    def _send_otp(self, purpose: str, role: Role, email: str) -> None:
        normalized = _normalize_email(email)
        self._ensure_email_allowed(purpose, normalized)
        now = utc_now()

        existing = self.otp_store.get(purpose, normalized)
        if existing and existing.next_send_at > now:
            raise ApiError(
                code=ErrorCode.OTP_RATE_LIMITED,
                message="OTP recently sent, try again later",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp_code = _generate_otp_code()
        challenge = OTPChallenge(
            purpose=purpose,
            target=normalized,
            otp_hash=hash_otp(normalized, otp_code),
            expires_at=expiry_from_now(self.settings.OTP_TTL_SECONDS),
            attempts_left=self.settings.OTP_MAX_ATTEMPTS,
            next_send_at=expiry_from_now(self.settings.OTP_RESEND_COOLDOWN_SECONDS),
        )
        self.otp_store.save(challenge)
        self.otp_notifier.send_otp(purpose, normalized, otp_code, self.settings.OTP_TTL_SECONDS)

        log.info(
            "otp_requested",
            extra={"purpose": purpose, "role": role.value, "target": _mask_email(normalized)},
        )

    def _verify_otp(self, purpose: str, role: Role, email: str, otp_code: str) -> AuthSession:
        normalized = _normalize_email(email)
        self._ensure_email_allowed(purpose, normalized)
        challenge = self.otp_store.get(purpose, normalized)

        if not challenge:
            raise ApiError(
                code=ErrorCode.OTP_INVALID,
                message="Invalid OTP",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        now = utc_now()
        if challenge.expires_at <= now:
            self.otp_store.delete(purpose, normalized)
            raise ApiError(
                code=ErrorCode.OTP_EXPIRED,
                message="OTP expired",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if challenge.attempts_left <= 0:
            self.otp_store.delete(purpose, normalized)
            raise ApiError(
                code=ErrorCode.OTP_ATTEMPTS_EXCEEDED,
                message="OTP attempts exceeded",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if challenge.otp_hash != hash_otp(normalized, otp_code):
            challenge.attempts_left -= 1
            self.otp_store.save(challenge)
            raise ApiError(
                code=ErrorCode.OTP_INVALID,
                message="Invalid OTP",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        self.otp_store.delete(purpose, normalized)
        token = generate_access_token(subject=normalized, role=role.value)
        expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        ).replace(microsecond=0)

        log.info(
            "otp_verified",
            extra={"purpose": purpose, "role": role.value, "target": _mask_email(normalized)},
        )

        return AuthSession(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at,
            role=role,
        )

    def _ensure_email_allowed(self, purpose: str, email: str) -> None:
        allowlist = self.settings.ADMIN_OTP_EMAILS if purpose == "admin" else self.settings.PORTAL_OTP_EMAILS
        allowed = {item.strip().lower() for item in allowlist.split(",") if item.strip()}
        if not allowed or email.lower() not in allowed:
            raise ApiError(
                code=ErrorCode.UNAUTHORIZED,
                message="Email is not allowed for this login flow",
                status_code=status.HTTP_403_FORBIDDEN,
            )


def _generate_otp_code() -> str:
    return f"{randbelow(1000000):06d}"


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid email format",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return normalized


def _mask_email(email: str) -> str:
    local, domain = email.split("@", maxsplit=1)
    if len(local) <= 2:
        local = "*" * len(local)
    else:
        local = local[:1] + ("*" * (len(local) - 2)) + local[-1:]
    return f"{local}@{domain}"

