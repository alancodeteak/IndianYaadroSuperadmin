from __future__ import annotations

import enum


class Role(str, enum.Enum):
    SUPERADMIN = "SUPERADMIN"
    PORTAL_USER = "PORTAL_USER"
    MONITOR_APP = "MONITOR_APP"

    @classmethod
    def from_str(cls, value: str) -> "Role":
        normalized = value.strip().upper()
        # Allow some aliases if token uses slightly different keys.
        if normalized in {"PORTAL", "PORTALUSER", "PORTAL_USER"}:
            return cls.PORTAL_USER
        if normalized in {"MONITOR", "MONITOR_APP", "MONITORAPP"}:
            return cls.MONITOR_APP
        if normalized in {"SUPERADMIN", "SUPER_ADMIN"}:
            return cls.SUPERADMIN
        return cls(normalized)

