from __future__ import annotations

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.order import OrderCreate, OrderUpdate
from app.api.core.constants import MAX_PAGE_SIZE
from app.domain.repositories.order_repository import AbstractOrderRepository
from app.infrastructure.db.models.order import Order


class OrderService:
    def __init__(self, repository: AbstractOrderRepository):
        self.repository = repository

    def list_orders(self, page: int, page_size: int) -> tuple[list[Order], int]:
        if page < 1:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="page must be >= 1",
                status_code=400,
            )
        if page_size < 1 or page_size > MAX_PAGE_SIZE:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"page_size must be between 1 and {MAX_PAGE_SIZE}",
                status_code=400,
            )
        items = self.repository.list_orders(page=page, page_size=page_size)
        total = self.repository.count_orders()
        return items, total

    def get_order(self, order_id: int) -> Order:
        item = self.repository.get_by_id(order_id)
        if not item:
            raise ApiError(
                code=ErrorCode.ORDER_NOT_FOUND,
                message="Order not found",
                status_code=404,
            )
        return item

    def create_order(self, payload: OrderCreate) -> Order:
        return self.repository.create_order(payload)

    def update_order(self, order_id: int, payload: OrderUpdate) -> Order:
        item = self.get_order(order_id)
        return self.repository.update_order(item, payload)

