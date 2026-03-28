from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.api.v1.schemas.shop_owner import (
    SupermarketCreateRequest,
    SupermarketListFilters,
    SupermarketUpdateRequest,
)


class AbstractShopOwnerRepository(ABC):
    @abstractmethod
    def list_supermarkets(
        self, page: int, limit: int, filters: SupermarketListFilters
    ) -> tuple[list[dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def get_shop_id_by_email(self, email: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def get_supermarket_detail_by_user_id(self, user_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def get_shop_activity_by_user_id(self, user_id: int, days: int) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def get_reports_overview(self, days: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_reports_shops(self, days: int, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_reports_funnel(self, days: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_reports_finance(self, days: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_supermarket(self, payload: SupermarketCreateRequest) -> str:
        """Persist supermarket (address + shop owner + optional subscription/promotion). Returns generated shop_id."""
        raise NotImplementedError

    @abstractmethod
    def update_supermarket(self, user_id: int, payload: SupermarketUpdateRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    def soft_delete_supermarket(self, user_id: int) -> None:
        raise NotImplementedError

