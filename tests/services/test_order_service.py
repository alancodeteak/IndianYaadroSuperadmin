from dataclasses import dataclass
from unittest.mock import MagicMock

from app.domain.enums.roles import Role
from app.domain.exceptions import DomainValidationError, NotFoundError
from app.services.order_service import OrderService


@dataclass
class _RepoStub:
    def list_orders_paginated(self, page: int, page_size: int, *, shop_id=None):
        return [], 0

    def get_by_id(self, order_id: int):
        return None

    def create_order(self, payload):
        return payload

    def update_order(self, order, payload):
        return order


def _shop_owner_stub():
    m = MagicMock()
    m.get_shop_id_by_email = MagicMock(return_value=None)
    return m


def _session_mock() -> MagicMock:
    s = MagicMock()
    s.commit = MagicMock()
    s.rollback = MagicMock()
    return s


def test_list_orders_rejects_invalid_page():
    service = OrderService(
        repository=_RepoStub(), session=_session_mock(), shop_owner_repository=_shop_owner_stub()
    )
    try:
        service.list_orders(role=Role.SUPERADMIN, user_id="admin@test", page=0, page_size=10)
        assert False, "Expected DomainValidationError for invalid page"
    except DomainValidationError as exc:
        assert exc.code == "VALIDATION_ERROR"


def test_get_order_not_found_raises():
    service = OrderService(
        repository=_RepoStub(), session=_session_mock(), shop_owner_repository=_shop_owner_stub()
    )
    try:
        service.get_order(role=Role.SUPERADMIN, user_id="a", order_id=9999)
        assert False, "Expected ORDER_NOT_FOUND"
    except NotFoundError as exc:
        assert exc.code == "ORDER_NOT_FOUND"
