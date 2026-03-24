from __future__ import annotations

from app.api.core.logger import get_logger

_otp_debug_log = get_logger("app.otp_debug")


def log_otp_code(*, purpose: str, target: str, otp_code: str, enabled: bool) -> None:
    """
    Dedicated OTP debug channel. Keep this separate from normal auth logs.
    """
    if not enabled:
        return
    _otp_debug_log.info(
        "otp_debug_code",
        extra={
            "purpose": purpose,
            "target": target,
            "otp_code": otp_code,
        },
    )

