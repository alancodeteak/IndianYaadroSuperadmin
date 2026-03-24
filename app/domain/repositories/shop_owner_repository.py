from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractShopOwnerRepository(ABC):
    @abstractmethod
    def list_supermarkets(self, page: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        raise NotImplementedError

