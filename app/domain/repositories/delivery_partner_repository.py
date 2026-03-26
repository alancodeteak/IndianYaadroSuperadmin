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

