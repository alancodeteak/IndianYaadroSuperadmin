from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ApiError(Exception):
    """
    Application-level error with stable code/message/detail contract.
    """

    code: str
    message: str
    status_code: int = 400
    details: Optional[dict[str, Any]] = None

    def __str__(self) -> str:  # pragma: no cover
        return f"ApiError(code={self.code}, status={self.status_code}): {self.message}"

