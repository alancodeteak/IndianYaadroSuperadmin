from __future__ import annotations

from app.api.core.logger import get_logger
from app.services.otp_service import OTPNotifier

log = get_logger(__name__)


class LogOTPNotifier(OTPNotifier):
    """
    Development-safe notifier: logs masked OTP delivery events.
    Replace with SMTP/provider adapter in production.
    """

    def send_otp(self, purpose: str, target: str, otp_code: str, expires_in_seconds: int) -> None:
        masked_target = _mask_target(target)
        log.info(
            "otp_dispatched",
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

