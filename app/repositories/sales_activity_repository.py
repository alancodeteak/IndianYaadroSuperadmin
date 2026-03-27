from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.enums import OrderStatus
from app.infrastructure.db.models.order import Order
from app.infrastructure.db.models.shop_owner import ShopOwner
from app.infrastructure.db.models.subscription import Subscription


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _day_start(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)


def _week_start(dt: datetime) -> datetime:
    start = _day_start(dt)
    return start - timedelta(days=start.weekday())


def _month_start(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)


def _add_months(dt: datetime, months: int) -> datetime:
    y = dt.year + (dt.month - 1 + months) // 12
    m = (dt.month - 1 + months) % 12 + 1
    return datetime(y, m, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class ForecastResult:
    next_month: str
    predicted_signups: float
    low: float
    high: float
    method: str


class SalesActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def _base_shops(self) -> list[Any]:
        return [ShopOwner.is_deleted.is_(False), ShopOwner.is_supermarket.is_(True)]

    def get_overview(self, *, days: int = 30) -> dict[str, Any]:
        now = _utc_now()
        today_start = _day_start(now)
        tomorrow_start = today_start + timedelta(days=1)
        week_start = _week_start(now)
        next_week_start = week_start + timedelta(days=7)
        month_start = _month_start(now)
        next_month_start = _add_months(month_start, 1)

        base = self._base_shops()

        def count_created(start: datetime, end: datetime) -> int:
            stmt = select(func.count(ShopOwner.id)).where(*base, ShopOwner.created_at >= start, ShopOwner.created_at < end)
            return int(self.db.scalar(stmt) or 0)

        today_count = count_created(today_start, tomorrow_start)
        week_count = count_created(week_start, next_week_start)
        month_count = count_created(month_start, next_month_start)

        # Previous periods for growth
        yesterday_start = today_start - timedelta(days=1)
        prev_week_start = week_start - timedelta(days=7)
        prev_month_start = _add_months(month_start, -1)
        prev_month_end = month_start

        yesterday_count = count_created(yesterday_start, today_start)
        prev_week_count = count_created(prev_week_start, week_start)
        prev_month_count = count_created(prev_month_start, prev_month_end)

        def growth(cur: int, prev: int) -> float:
            if prev <= 0:
                return 100.0 if cur > 0 else 0.0
            return (cur - prev) * 100.0 / prev

        kpis = {
            "today_signups": today_count,
            "week_signups": week_count,
            "month_signups": month_count,
            "today_growth_pct": growth(today_count, yesterday_count),
            "week_growth_pct": growth(week_count, prev_week_count),
            "month_growth_pct": growth(month_count, prev_month_count),
        }

        # Trend: created shops per day
        days = max(7, min(int(days), 90))
        since = _day_start(now) - timedelta(days=days - 1)
        trend_stmt = (
            select(func.date(ShopOwner.created_at).label("date"), func.count(ShopOwner.id).label("count"))
            .where(*base, ShopOwner.created_at >= since, ShopOwner.created_at < tomorrow_start)
            .group_by(func.date(ShopOwner.created_at))
            .order_by(func.date(ShopOwner.created_at))
        )
        trend_rows = self.db.execute(trend_stmt).all()
        signups_daily = [{"date": str(r.date), "count": int(r.count or 0)} for r in trend_rows]

        # Activation: time-to-first-order buckets (first order any status, not deleted)
        first_order_subq = (
            select(Order.shop_id.label("shop_id"), func.min(Order.created_at).label("first_order_at"))
            .where(Order.is_deleted.is_(False))
            .group_by(Order.shop_id)
            .subquery()
        )

        cohort_shops_stmt = (
            select(
                ShopOwner.shop_id,
                ShopOwner.created_at,
                first_order_subq.c.first_order_at,
            )
            .outerjoin(first_order_subq, first_order_subq.c.shop_id == ShopOwner.shop_id)
            .where(*base, ShopOwner.created_at >= since, ShopOwner.created_at < tomorrow_start)
        )
        rows = self.db.execute(cohort_shops_stmt).all()

        buckets = {"0_1d": 0, "1_3d": 0, "3_7d": 0, "gt_7d": 0, "never": 0}
        ttf_minutes: list[float] = []
        for r in rows:
            created_at = r.created_at
            first_at = r.first_order_at
            if not first_at:
                buckets["never"] += 1
                continue
            delta = first_at - created_at
            mins = delta.total_seconds() / 60.0
            if mins >= 0:
                ttf_minutes.append(mins)
            hours = delta.total_seconds() / 3600.0
            if hours <= 24:
                buckets["0_1d"] += 1
            elif hours <= 72:
                buckets["1_3d"] += 1
            elif hours <= 168:
                buckets["3_7d"] += 1
            else:
                buckets["gt_7d"] += 1

        activated = sum(buckets[k] for k in ("0_1d", "1_3d", "3_7d", "gt_7d"))
        total = activated + buckets["never"]
        activation_rate = (activated * 100.0 / total) if total else 0.0

        # Median time-to-first-order (mins)
        ttf_minutes_sorted = sorted(ttf_minutes)
        median_ttf_mins = 0.0
        if ttf_minutes_sorted:
            mid = len(ttf_minutes_sorted) // 2
            median_ttf_mins = (
                (ttf_minutes_sorted[mid - 1] + ttf_minutes_sorted[mid]) / 2.0
                if len(ttf_minutes_sorted) % 2 == 0
                else ttf_minutes_sorted[mid]
            )

        return {
            "kpis": kpis,
            "trend": {"signups_daily": signups_daily, "window_days": days},
            "activation": {
                "activation_rate_pct": activation_rate,
                "median_time_to_first_order_mins": median_ttf_mins,
                "time_to_first_order_buckets": buckets,
            },
        }

    def get_monthly(self, *, months: int = 6) -> list[dict[str, Any]]:
        now = _utc_now()
        months = max(3, min(int(months), 12))
        start_month = _add_months(_month_start(now), -(months - 1))
        end_month = _add_months(_month_start(now), 1)

        base = self._base_shops()

        # Created shops per month
        created_stmt = (
            select(
                func.date_trunc("month", ShopOwner.created_at).label("month"),
                func.count(ShopOwner.id).label("shops_created"),
            )
            .where(*base, ShopOwner.created_at >= start_month, ShopOwner.created_at < end_month)
            .group_by(func.date_trunc("month", ShopOwner.created_at))
            .order_by(func.date_trunc("month", ShopOwner.created_at))
        )
        created_rows = {str(r.month.date()): int(r.shops_created or 0) for r in self.db.execute(created_stmt).all()}

        # Cohort: orders in same month for shops created that month
        # and orders in first 30 days for shops created that month.
        cohort_stmt = (
            select(
                func.date_trunc("month", ShopOwner.created_at).label("month"),
                func.count(distinct(ShopOwner.shop_id)).label("shops"),
                func.count(Order.order_id).label("orders_first_30d"),
                func.coalesce(
                    func.sum(case((Order.order_status == OrderStatus.DELIVERED, Order.total_amount), else_=0)),
                    0,
                ).label("delivered_revenue_first_30d"),
                func.sum(
                    case(
                        (
                            func.date_trunc("month", Order.created_at) == func.date_trunc("month", ShopOwner.created_at),
                            1,
                        ),
                        else_=0,
                    )
                ).label("orders_same_month"),
            )
            .join(Order, Order.shop_id == ShopOwner.shop_id)
            .where(
                *base,
                Order.is_deleted.is_(False),
                ShopOwner.created_at >= start_month,
                ShopOwner.created_at < end_month,
                Order.created_at >= ShopOwner.created_at,
                Order.created_at < (ShopOwner.created_at + timedelta(days=30)),
            )
            .group_by(func.date_trunc("month", ShopOwner.created_at))
            .order_by(func.date_trunc("month", ShopOwner.created_at))
        )
        cohort_rows = self.db.execute(cohort_stmt).all()
        cohort_map: dict[str, dict[str, Any]] = {
            str(r.month.date()): {
                "orders_first_30d": int(r.orders_first_30d or 0),
                "orders_same_month": int(r.orders_same_month or 0),
                "delivered_revenue_first_30d": float(r.delivered_revenue_first_30d or 0),
            }
            for r in cohort_rows
        }

        # Subscription amount sum for shops created that month
        sub_stmt = (
            select(
                func.date_trunc("month", ShopOwner.created_at).label("month"),
                func.coalesce(func.sum(Subscription.amount), 0).label("subscription_amount_sum"),
            )
            .join(Subscription, Subscription.shop_id == ShopOwner.shop_id, isouter=True)
            .where(*base, ShopOwner.created_at >= start_month, ShopOwner.created_at < end_month)
            .group_by(func.date_trunc("month", ShopOwner.created_at))
            .order_by(func.date_trunc("month", ShopOwner.created_at))
        )
        sub_rows = {str(r.month.date()): float(r.subscription_amount_sum or 0) for r in self.db.execute(sub_stmt).all()}

        # Normalize to full month series
        out: list[dict[str, Any]] = []
        cursor = start_month
        while cursor < end_month:
            key = str(cursor.date())
            out.append(
                {
                    "month": key[:7],
                    "shops_created": int(created_rows.get(key, 0)),
                    "orders_first_30d": int(cohort_map.get(key, {}).get("orders_first_30d", 0)),
                    "orders_same_month": int(cohort_map.get(key, {}).get("orders_same_month", 0)),
                    "delivered_revenue_first_30d": float(cohort_map.get(key, {}).get("delivered_revenue_first_30d", 0)),
                    "subscription_amount_sum": float(sub_rows.get(key, 0)),
                }
            )
            cursor = _add_months(cursor, 1)
        return out

    def get_top_shops_last_3_months(self, *, limit: int = 20) -> list[dict[str, Any]]:
        now = _utc_now()
        m0 = _month_start(now)
        m1 = _add_months(m0, -1)
        m2 = _add_months(m0, -2)
        m3 = _add_months(m0, 1)

        stmt = (
            select(
                ShopOwner.shop_id,
                ShopOwner.shop_name,
                ShopOwner.user_id,
                func.sum(case((Order.created_at >= m2, 1), else_=0)).label("m2_total"),
                func.sum(case((Order.created_at >= m1, 1), else_=0)).label("m1_total"),
                func.sum(case((Order.created_at >= m0, 1), else_=0)).label("m0_total"),
            )
            .join(Order, Order.shop_id == ShopOwner.shop_id)
            .where(*self._base_shops(), Order.is_deleted.is_(False), Order.created_at >= m2, Order.created_at < m3)
            .group_by(ShopOwner.shop_id, ShopOwner.shop_name, ShopOwner.user_id)
            .order_by(func.sum(case((Order.created_at >= m0, 1), else_=0)).desc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        items: list[dict[str, Any]] = []
        for r in rows:
            items.append(
                {
                    "shop_id": str(r.shop_id),
                    "shop_name": str(r.shop_name),
                    "user_id": int(r.user_id),
                    "months": {
                        str(m2.date())[:7]: int(r.m2_total or 0),
                        str(m1.date())[:7]: int(r.m1_total or 0),
                        str(m0.date())[:7]: int(r.m0_total or 0),
                    },
                }
            )
        return items

    def forecast_next_month_signups(self, *, months_back: int = 6) -> ForecastResult:
        now = _utc_now()
        months_back = max(3, min(int(months_back), 12))
        start_month = _add_months(_month_start(now), -(months_back - 1))
        end_month = _add_months(_month_start(now), 1)

        stmt = (
            select(func.date_trunc("month", ShopOwner.created_at).label("month"), func.count(ShopOwner.id).label("count"))
            .where(*self._base_shops(), ShopOwner.created_at >= start_month, ShopOwner.created_at < end_month)
            .group_by(func.date_trunc("month", ShopOwner.created_at))
            .order_by(func.date_trunc("month", ShopOwner.created_at))
        )
        rows = self.db.execute(stmt).all()
        series = [int(r.count or 0) for r in rows]
        if not series:
            next_month = _add_months(_month_start(now), 1)
            return ForecastResult(next_month=str(next_month.date())[:7], predicted_signups=0.0, low=0.0, high=0.0, method="moving_avg")

        # Moving average forecast (simple and stable)
        window = min(3, len(series))
        avg = sum(series[-window:]) / float(window)
        # Volatility band: +- max(10%, std-ish approx)
        low = max(0.0, avg * 0.85)
        high = avg * 1.15
        next_month = _add_months(_month_start(now), 1)
        return ForecastResult(
            next_month=str(next_month.date())[:7],
            predicted_signups=float(avg),
            low=float(low),
            high=float(high),
            method="moving_avg_3",
        )

