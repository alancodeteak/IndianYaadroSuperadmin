from functools import lru_cache

from app.api.core.config import Settings, get_settings
from app.infrastructure.otp_notifier import SMTPOTPNotifier
from app.services.otp_service import InMemoryOTPStore, OTPNotifier


@lru_cache
def get_otp_store() -> InMemoryOTPStore:
    return InMemoryOTPStore()


@lru_cache
def get_otp_notifier() -> OTPNotifier:
    settings: Settings = get_settings()
    return SMTPOTPNotifier(settings=settings)

