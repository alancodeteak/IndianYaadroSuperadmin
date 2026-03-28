from __future__ import annotations

from app.api.v1.schemas.order import OrderCreate, OrderUpdate
from app.api.core.constants import MAX_PAGE_SIZE
from app.api.exceptions.error_codes import ErrorCode
from app.domain.exceptions import NotFoundError
from app.domain.repositories.order_repository import AbstractOrderRepository
from app.infrastructure.db.models.order import Order
from app.services.validation import validate_page_and_limit


class OrderService:
    def __init__(self, repository: AbstractOrderRepository):
        self.repository = repository

    def list_orders(self, page: int, page_size: int) -> tuple[list[Order], int]:
        validate_page_and_limit(page, page_size, max_limit=MAX_PAGE_SIZE)
        return self.repository.list_orders_paginated(page=page, page_size=page_size)

    def get_order(self, order_id: int) -> Order:
        item = self.repository.get_by_id(order_id)
        if not item:
            raise NotFoundError("Order not found", code=ErrorCode.ORDER_NOT_FOUND)
        return item

    def create_order(self, payload: OrderCreate) -> Order:
        return self.repository.create_order(payload)

    def update_order(self, order_id: int, payload: OrderUpdate) -> Order:
        item = self.get_order(order_id)
        return self.repository.update_order(item, payload)

