from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.api.v1.schemas.shop_owner import SupermarketListFilters


class AbstractShopOwnerRepository(ABC):
    @abstractmethod
    def list_supermarkets(
        self, page: int, limit: int, filters: SupermarketListFilters
    ) -> tuple[list[dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def get_supermarket_detail_by_user_id(self, user_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

