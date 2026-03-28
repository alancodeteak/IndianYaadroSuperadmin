from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.api.v1.schemas.order import OrderCreate, OrderUpdate
from app.api.core.constants import MAX_PAGE_SIZE
from app.api.exceptions.error_codes import ErrorCode
from app.domain.enums.roles import Role
from app.domain.exceptions import NotFoundError, PermissionDeniedError
from app.domain.repositories.order_repository import AbstractOrderRepository
from app.domain.repositories.shop_owner_repository import AbstractShopOwnerRepository
from app.infrastructure.db.models.order import Order
from app.infrastructure.db.transaction import session_commit_scope
from app.services.validation import validate_page_and_limit

log = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self,
        repository: AbstractOrderRepository,
        session: Session,
        shop_owner_repository: AbstractShopOwnerRepository,
    ):
        self.repository = repository
        self._session = session
        self._shop_owner_repository = shop_owner_repository

    def list_orders(
        self, *, role: Role, user_id: str, page: int, page_size: int
    ) -> tuple[list[Order], int]:
        validate_page_and_limit(page, page_size, max_limit=MAX_PAGE_SIZE)
        shop_id: str | None = None
        if role == Role.PORTAL_USER:
            shop_id = self._shop_owner_repository.get_shop_id_by_email(user_id)
            if not shop_id:
                log.info("list_orders portal user has no mapped shop", extra={"user_id": user_id})
                return [], 0
        elif role == Role.SUPERADMIN:
            shop_id = None
        elif role == Role.MONITOR_APP:
            shop_id = None
        else:
            raise PermissionDeniedError("Not enough permissions")

        return self.repository.list_orders_paginated(page=page, page_size=page_size, shop_id=shop_id)

    def get_order(self, *, role: Role, user_id: str, order_id: int) -> Order:
        item = self.repository.get_by_id(order_id)
        if not item:
            raise NotFoundError("Order not found", code=ErrorCode.ORDER_NOT_FOUND)
        if role == Role.PORTAL_USER:
            shop_id = self._shop_owner_repository.get_shop_id_by_email(user_id)
            if not shop_id or item.shop_id != shop_id:
                log.info(
                    "get_order denied for portal user",
                    extra={"order_id": order_id, "user_id": user_id},
                )
                raise PermissionDeniedError("Not enough permissions")
        elif role == Role.SUPERADMIN:
            pass
        elif role == Role.MONITOR_APP:
            pass
        else:
            raise PermissionDeniedError("Not enough permissions")
        return item

    def create_order(self, *, role: Role, user_id: str, payload: OrderCreate) -> Order:
        if role == Role.MONITOR_APP:
            raise PermissionDeniedError("Not enough permissions")
        if role == Role.PORTAL_USER:
            shop_id = self._shop_owner_repository.get_shop_id_by_email(user_id)
            if not shop_id or payload.shop_id != shop_id:
                log.info(
                    "create_order denied portal wrong shop",
                    extra={"user_id": user_id, "payload_shop_id": getattr(payload, "shop_id", None)},
                )
                raise PermissionDeniedError("Not enough permissions")
        elif role != Role.SUPERADMIN:
            raise PermissionDeniedError("Not enough permissions")
        with session_commit_scope(self._session):
            return self.repository.create_order(payload)

    def update_order(
        self, *, role: Role, user_id: str, order_id: int, payload: OrderUpdate
    ) -> Order:
        if role == Role.MONITOR_APP:
            raise PermissionDeniedError("Not enough permissions")
        item = self.get_order(role=role, user_id=user_id, order_id=order_id)
        with session_commit_scope(self._session):
            return self.repository.update_order(item, payload)
