from __future__ import annotations

import smtplib
from email.message import EmailMessage

from starlette import status

from app.api.core.config import Settings
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.core.logger import get_logger
from app.services.otp_service import OTPNotifier

log = get_logger(__name__)


class SMTPOTPNotifier(OTPNotifier):
    """
    SMTP notifier for OTP delivery.
    Does not log OTP values.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def send_otp(self, purpose: str, target: str, otp_code: str, expires_in_seconds: int) -> None:
        if not self.settings.SMTP_ENABLED:
            self._log_fallback(purpose, target, expires_in_seconds, otp_code)
            return

        masked_target = _mask_target(target)
        msg = EmailMessage()
        msg["Subject"] = f"Your Yadro OTP ({purpose})"
        msg["From"] = _from_header(self.settings.SMTP_FROM_NAME, self.settings.SMTP_FROM_EMAIL)
        msg["To"] = target
        msg.set_content(
            f"Your OTP code is: {otp_code}\n"
            f"This code expires in {expires_in_seconds} seconds.\n"
            "If you did not request this OTP, please ignore this email."
        )

        try:
            if self.settings.SMTP_USE_SSL:
                with smtplib.SMTP_SSL(
                    host=self.settings.SMTP_HOST,
                    port=self.settings.SMTP_PORT,
                    timeout=10,
                ) as client:
                    client.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                    client.send_message(msg)
            else:
                with smtplib.SMTP(
                    host=self.settings.SMTP_HOST,
                    port=self.settings.SMTP_PORT,
                    timeout=10,
                ) as client:
                    if self.settings.SMTP_USE_TLS:
                        client.starttls()
                    client.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                    client.send_message(msg)
        except Exception:
            log.exception(
                "otp_dispatch_failed",
                extra={
                    "purpose": purpose,
                    "target": masked_target,
                    "smtp_host": self.settings.SMTP_HOST,
                },
            )
            raise ApiError(
                code=ErrorCode.OTP_DELIVERY_FAILED,
                message="Unable to deliver OTP at the moment",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        log.info(
            "otp_dispatched",
            extra={
                "purpose": purpose,
                "target": masked_target,
                "expires_in_seconds": expires_in_seconds,
                "otp_length": len(otp_code),
            },
        )

    def _log_fallback(
        self, purpose: str, target: str, expires_in_seconds: int, otp_code: str
    ) -> None:
        masked_target = _mask_target(target)
        log.info(
            "otp_dispatched_fallback",
            extra={
                "purpose": purpose,
                "target": masked_target,
                "expires_in_seconds": expires_in_seconds,
                "otp_length": len(otp_code),
            },
        )


def _mask_target(target: str) -> str:
    if "@" not in target:
        return "***"
    local, domain = target.split("@", maxsplit=1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + ("*" * (len(local) - 2)) + local[-1]
    return f"{masked_local}@{domain}"


def _from_header(name: str, email: str) -> str:
    clean_name = name.strip()
    if clean_name:
        return f"{clean_name} <{email}>"
    return email

