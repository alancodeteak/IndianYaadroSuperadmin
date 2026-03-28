from dataclasses import dataclass

from app.api.exceptions.http_errors import ApiError
from app.domain.exceptions import NotFoundError
from app.services.order_service import OrderService


@dataclass
class _RepoStub:
    def list_orders_paginated(self, page: int, page_size: int):
        return [], 0

    def get_by_id(self, order_id: int):
        return None

    def create_order(self, payload):
        return payload

    def update_order(self, order, payload):
        return order


def test_list_orders_rejects_invalid_page():
    service = OrderService(repository=_RepoStub())
    try:
        service.list_orders(page=0, page_size=10)
        assert False, "Expected ApiError for invalid page"
    except ApiError as exc:
        assert exc.code == "VALIDATION_ERROR"


def test_get_order_not_found_raises():
    service = OrderService(repository=_RepoStub())
    try:
        service.get_order(order_id=9999)
        assert False, "Expected ORDER_NOT_FOUND"
    except NotFoundError as exc:
        assert exc.code == "ORDER_NOT_FOUND"
