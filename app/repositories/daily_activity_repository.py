from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.enums import OrderStatus
from app.infrastructure.db.models.order import Order
from app.infrastructure.db.models.shop_owner import ShopOwner


def _day_bounds(target_date: date, tz: timezone = timezone.utc) -> tuple[datetime, datetime]:
    start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end


class DailyActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(self, *, target_date: date, tz: timezone = timezone.utc) -> dict[str, Any]:
        start, end = _day_bounds(target_date, tz)

        base = [Order.is_deleted.is_(False), Order.created_at >= start, Order.created_at < end]

        total_orders_stmt = select(func.count(Order.order_id)).where(*base)
        total_orders = int(self.db.scalar(total_orders_stmt) or 0)

        delivered_revenue_stmt = select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            *base, Order.order_status == OrderStatus.DELIVERED
        )
        delivered_revenue = float(self.db.scalar(delivered_revenue_stmt) or 0)

        active_shops_stmt = select(func.count(distinct(Order.shop_id))).where(*base)
        active_shops = int(self.db.scalar(active_shops_stmt) or 0)

        status_stmt = (
            select(Order.order_status, func.count(Order.order_id).label("count"))
            .where(*base)
            .group_by(Order.order_status)
        )
        status_rows = self.db.execute(status_stmt).all()
        status_counts = {str(r.order_status.value): int(r.count or 0) for r in status_rows}

        # SLA (minutes) for orders created that day with timestamps present.
        # Use avg of (timestamp - created_at).
        def avg_minutes(col):
            return func.avg(func.extract("epoch", col - Order.created_at) / 60.0)

        sla_stmt = select(
            func.coalesce(avg_minutes(Order.assigned_at), 0).label("avg_assign_mins"),
            func.coalesce(avg_minutes(Order.picked_up_at), 0).label("avg_pickup_mins"),
            func.coalesce(avg_minutes(Order.delivered_at), 0).label("avg_deliver_mins"),
        ).where(*base)

        sla = self.db.execute(sla_stmt).one()

        return {
            "date": str(target_date),
            "kpis": {
                "total_orders": total_orders,
                "delivered_revenue": delivered_revenue,
                "active_shops": active_shops,
            },
            "status_counts": status_counts,
            "sla": {
                "avg_assign_mins": float(sla.avg_assign_mins or 0),
                "avg_pickup_mins": float(sla.avg_pickup_mins or 0),
                "avg_deliver_mins": float(sla.avg_deliver_mins or 0),
            },
        }

    def list_shops(
        self,
        *,
        target_date: date,
        page: int,
        limit: int,
        search: str | None = None,
        sort: str = "revenue_desc",
        tz: timezone = timezone.utc,
    ) -> tuple[list[dict[str, Any]], int]:
        start, end = _day_bounds(target_date, tz)

        base = [Order.is_deleted.is_(False), Order.created_at >= start, Order.created_at < end]
        if search and search.strip():
            q = f"%{search.strip()}%"
            base.append(ShopOwner.shop_name.ilike(q))

        delivered_amount = func.coalesce(
            func.sum(case((Order.order_status == OrderStatus.DELIVERED, Order.total_amount), else_=0)),
            0,
        ).label("delivered_revenue")
        total_orders = func.count(Order.order_id).label("total_orders")
        delivered_orders = func.sum(case((Order.order_status == OrderStatus.DELIVERED, 1), else_=0)).label(
            "delivered_orders"
        )
        cancelled_orders = func.sum(case((Order.order_status == OrderStatus.CANCELLED, 1), else_=0)).label(
            "cancelled_orders"
        )
        last_order_at = func.max(Order.created_at).label("last_order_at")

        avg_assign_mins = func.avg(func.extract("epoch", Order.assigned_at - Order.created_at) / 60.0).label(
            "avg_assign_mins"
        )
        avg_pickup_mins = func.avg(func.extract("epoch", Order.picked_up_at - Order.created_at) / 60.0).label(
            "avg_pickup_mins"
        )
        avg_deliver_mins = func.avg(func.extract("epoch", Order.delivered_at - Order.created_at) / 60.0).label(
            "avg_deliver_mins"
        )

        stmt = (
            select(
                Order.shop_id,
                ShopOwner.shop_name,
                ShopOwner.user_id,
                total_orders,
                delivered_orders,
                cancelled_orders,
                delivered_amount,
                last_order_at,
                func.coalesce(avg_assign_mins, 0),
                func.coalesce(avg_pickup_mins, 0),
                func.coalesce(avg_deliver_mins, 0),
            )
            .join(ShopOwner, ShopOwner.shop_id == Order.shop_id)
            .where(*base)
            .group_by(Order.shop_id, ShopOwner.shop_name, ShopOwner.user_id)
        )

        if sort == "orders_desc":
            stmt = stmt.order_by(total_orders.desc())
        elif sort == "sla_deliver_desc":
            stmt = stmt.order_by(func.coalesce(avg_deliver_mins, 0).desc())
        else:
            stmt = stmt.order_by(delivered_amount.desc())

        count_stmt = select(func.count(distinct(Order.shop_id))).join(ShopOwner, ShopOwner.shop_id == Order.shop_id).where(
            *base
        )
        total = int(self.db.scalar(count_stmt) or 0)

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        rows = self.db.execute(stmt).all()
        items = [
            {
                "shop_id": str(r.shop_id),
                "shop_name": str(r.shop_name),
                "user_id": int(r.user_id),
                "total_orders": int(r.total_orders or 0),
                "delivered_orders": int(r.delivered_orders or 0),
                "cancelled_orders": int(r.cancelled_orders or 0),
                "delivered_revenue": float(r.delivered_revenue or 0),
                "last_order_at": r.last_order_at.isoformat() if r.last_order_at else None,
                "sla": {
                    "avg_assign_mins": float(r[8] or 0),
                    "avg_pickup_mins": float(r[9] or 0),
                    "avg_deliver_mins": float(r[10] or 0),
                },
            }
            for r in rows
        ]
        return items, total

    def get_trends(self, *, days: int, tz: timezone = timezone.utc) -> list[dict[str, Any]]:
        days = max(1, min(int(days), 90))
        end = datetime.now(tz)
        start = end - timedelta(days=days)

        base = [Order.is_deleted.is_(False), Order.created_at >= start, Order.created_at < end]

        stmt = (
            select(
                func.date(Order.created_at).label("date"),
                func.count(Order.order_id).label("orders"),
                func.coalesce(
                    func.sum(case((Order.order_status == OrderStatus.DELIVERED, Order.total_amount), else_=0)),
                    0,
                ).label("delivered_revenue"),
            )
            .where(*base)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        rows = self.db.execute(stmt).all()
        return [{"date": str(r.date), "orders": int(r.orders or 0), "delivered_revenue": float(r.delivered_revenue or 0)} for r in rows]

