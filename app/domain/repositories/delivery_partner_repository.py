from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.api.v1.schemas.delivery_partner import DeliveryPartnerListFilters


class AbstractDeliveryPartnerRepository(ABC):
    @abstractmethod
    def list_delivery_partners(
        self, page: int, limit: int, filters: DeliveryPartnerListFilters
    ) -> tuple[list[dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def get_delivery_partner_detail(self, delivery_partner_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def set_delivery_partner_blocked(self, delivery_partner_id: str, *, blocked: bool) -> bool:
        """Returns True if updated, False if not found (or deleted)."""
        raise NotImplementedError

    @abstractmethod
    def soft_delete_delivery_partner(self, delivery_partner_id: str) -> bool:
        """Returns True if deleted, False if not found (or already deleted)."""
        raise NotImplementedError

    @abstractmethod
    def restore_delivery_partner(self, delivery_partner_id: str) -> bool:
        """Returns True if restored, False if not found (or not deleted)."""
        raise NotImplementedError

