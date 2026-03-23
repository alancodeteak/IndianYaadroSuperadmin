from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Protocol


@dataclass
class OTPChallenge:
    purpose: str
    target: str
    otp_hash: str
    expires_at: datetime
    attempts_left: int
    next_send_at: datetime


class OTPStore(Protocol):
    def get(self, purpose: str, target: str) -> OTPChallenge | None: ...
    def save(self, challenge: OTPChallenge) -> None: ...
    def delete(self, purpose: str, target: str) -> None: ...


class OTPNotifier(Protocol):
    def send_otp(self, purpose: str, target: str, otp_code: str, expires_in_seconds: int) -> None: ...


class InMemoryOTPStore:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], OTPChallenge] = {}

    def get(self, purpose: str, target: str) -> OTPChallenge | None:
        return self._items.get((purpose, target))

    def save(self, challenge: OTPChallenge) -> None:
        self._items[(challenge.purpose, challenge.target)] = challenge

    def delete(self, purpose: str, target: str) -> None:
        self._items.pop((purpose, target), None)


def hash_otp(target: str, otp_code: str) -> str:
    return sha256(f"{target}:{otp_code}".encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def expiry_from_now(ttl_seconds: int) -> datetime:
    return utc_now() + timedelta(seconds=ttl_seconds)

