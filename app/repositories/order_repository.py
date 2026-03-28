from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.schemas.order import OrderCreate, OrderUpdate
from app.domain.repositories.order_repository import AbstractOrderRepository
from app.infrastructure.db.models.order import Order


class OrderRepository(AbstractOrderRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_orders_paginated(
        self, page: int, page_size: int, *, shop_id: str | None = None
    ) -> tuple[list[Order], int]:
        stmt = select(Order, func.count().over().label("_total"))
        if shop_id is not None:
            stmt = stmt.where(Order.shop_id == shop_id)
        stmt = stmt.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = list(self.db.execute(stmt).all())
        if not rows:
            count_stmt = select(func.count()).select_from(Order)
            if shop_id is not None:
                count_stmt = count_stmt.where(Order.shop_id == shop_id)
            total = int(self.db.scalar(count_stmt) or 0)
            return [], total
        items = [r[0] for r in rows]
        total = int(rows[0][1])
        return items, total

    def get_by_id(self, order_id: int) -> Order | None:
        return self.db.get(Order, order_id)

    def create_order(self, payload: OrderCreate) -> Order:
        order = Order(**payload.model_dump())
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)
        return order

    def update_order(self, order: Order, payload: OrderUpdate) -> Order:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(order, key, value)
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)
        return order
