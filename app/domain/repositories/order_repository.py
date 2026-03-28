from __future__ import annotations

from abc import ABC, abstractmethod

from app.api.v1.schemas.order import OrderCreate, OrderUpdate
from app.infrastructure.db.models.order import Order


class AbstractOrderRepository(ABC):
    @abstractmethod
    def list_orders_paginated(
        self, page: int, page_size: int, *, shop_id: str | None = None
    ) -> tuple[list[Order], int]:
        """Return page of orders and total count (window count when rows exist; shop_id scopes portal)."""

    @abstractmethod
    def get_by_id(self, order_id: int) -> Order | None:
        raise NotImplementedError

    @abstractmethod
    def create_order(self, payload: OrderCreate) -> Order:
        raise NotImplementedError

    @abstractmethod
    def update_order(self, order: Order, payload: OrderUpdate) -> Order:
        raise NotImplementedError

