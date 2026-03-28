from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import String, case, cast, distinct, func, literal, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.enums import OrderStatus
from app.infrastructure.db.models.order import Order
from app.infrastructure.db.models.shop_owner import ShopOwner

# Postgres enum labels match Python enum *values* ("Delivered", "cancelled", …). Comparing the ORM
# column to plain strings still gets coerced to Python Enum and binds as member names (e.g. DELIVERED),
# which Postgres rejects — compare as text + literal instead.
_OS_DELIVERED = OrderStatus.DELIVERED.value


def _order_status_is(value: str):
    return cast(Order.order_status, String) == literal(value, type_=String())


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
            *base, _order_status_is(_OS_DELIVERED)
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
        """All supermarkets with shop record status; order stats for the day (zeros if none)."""
        start, end = _day_bounds(target_date, tz)

        order_filters = [
            Order.is_deleted.is_(False),
            Order.created_at >= start,
            Order.created_at < end,
        ]

        total_orders = func.count(Order.order_id).label("total_orders")
        total_revenue = func.coalesce(func.sum(Order.total_amount), 0).label("total_revenue")

        order_agg = (
            select(
                Order.shop_id.label("shop_id"),
                total_orders,
                total_revenue,
            )
            .where(*order_filters)
            .group_by(Order.shop_id)
        ).subquery()

        shop_filters = [
            ShopOwner.is_supermarket.is_(True),
            ShopOwner.is_deleted.is_(False),
        ]
        if search and search.strip():
            q = f"%{search.strip()}%"
            shop_filters.append(ShopOwner.shop_name.ilike(q))

        oa = order_agg.alias("oa")
        rev_sort = func.coalesce(oa.c.total_revenue, 0)
        orders_sort = func.coalesce(oa.c.total_orders, 0)

        stmt = (
            select(
                ShopOwner.shop_name,
                ShopOwner.user_id,
                func.coalesce(oa.c.total_orders, 0).label("total_orders"),
                func.coalesce(oa.c.total_revenue, 0).label("total_revenue"),
            )
            .select_from(ShopOwner)
            .outerjoin(oa, ShopOwner.shop_id == oa.c.shop_id)
            .where(*shop_filters)
        )

        if sort == "orders_desc":
            stmt = stmt.order_by(orders_sort.desc(), ShopOwner.shop_name.asc())
        elif sort == "name_asc":
            stmt = stmt.order_by(ShopOwner.shop_name.asc())
        else:
            stmt = stmt.order_by(rev_sort.desc(), ShopOwner.shop_name.asc())

        count_stmt = select(func.count()).select_from(ShopOwner).where(*shop_filters)
        total = int(self.db.scalar(count_stmt) or 0)

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        rows = self.db.execute(stmt).all()
        items = [
            {
                "shop_name": str(r.shop_name),
                "user_id": int(r.user_id),
                "total_orders": int(r.total_orders or 0),
                "total_revenue": float(r.total_revenue or 0),
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
                    func.sum(case((_order_status_is(_OS_DELIVERED), Order.total_amount), else_=0)),
                    0,
                ).label("delivered_revenue"),
            )
            .where(*base)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        rows = self.db.execute(stmt).all()
        return [{"date": str(r.date), "orders": int(r.orders or 0), "delivered_revenue": float(r.delivered_revenue or 0)} for r in rows]

