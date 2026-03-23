from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.schemas.order import OrderCreate, OrderUpdate
from app.domain.repositories.order_repository import AbstractOrderRepository
from app.infrastructure.db.models.order import Order


class OrderRepository(AbstractOrderRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_orders(self, page: int, page_size: int) -> list[Order]:
        stmt = (
            select(Order)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all())

    def count_orders(self) -> int:
        stmt = select(func.count(Order.order_id))
        return int(self.db.scalar(stmt) or 0)

    def get_by_id(self, order_id: int) -> Order | None:
        return self.db.get(Order, order_id)

    def create_order(self, payload: OrderCreate) -> Order:
        order = Order(**payload.model_dump())
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def update_order(self, order: Order, payload: OrderUpdate) -> Order:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(order, key, value)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

