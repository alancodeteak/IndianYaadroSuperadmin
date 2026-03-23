from __future__ import annotations

from datetime import datetime, timezone


class SessionService:
    def __init__(self) -> None:
        self._revoked_until: dict[str, int] = {}

    def revoke_jti(self, jti: str, exp_timestamp: int) -> None:
        self._revoked_until[jti] = exp_timestamp

    def is_revoked(self, jti: str) -> bool:
        exp = self._revoked_until.get(jti)
        if exp is None:
            return False

        now_ts = int(datetime.now(timezone.utc).timestamp())
        if now_ts > exp:
            self._revoked_until.pop(jti, None)
            return False
        return True

