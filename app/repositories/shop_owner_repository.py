from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import String, case, cast, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.shop_owner import (
    SupermarketCreateRequest,
    SupermarketListFilters,
    SupermarketUpdateRequest,
)
from app.domain.repositories.shop_owner_repository import AbstractShopOwnerRepository
from app.infrastructure.db.models.address import Address
from app.infrastructure.db.models.delivery_partner import DeliveryPartner
from app.infrastructure.db.models.enums import ShopPaymentStatus, ShopStatus, SubscriptionStatus
from app.infrastructure.db.models.order import Order
from app.infrastructure.db.models.shop_owner import ShopOwner
from app.infrastructure.db.models.shop_owner_promotion import ShopOwnerPromotion
from app.infrastructure.db.models.subscription import Subscription
from app.infrastructure.db.models.subscription_invoice import SubscriptionInvoice
from app.infrastructure.storage.s3 import is_http_url, presigned_get_url


class ShopOwnerRepository(AbstractShopOwnerRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_supermarkets(
        self, page: int, limit: int, filters: SupermarketListFilters
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = [
            ShopOwner.is_supermarket.is_(True),
            ShopOwner.is_deleted.is_(False),
        ]
        if filters.name:
            conditions.append(ShopOwner.shop_name.ilike(f"%{filters.name.strip()}%"))
        if filters.user_id is not None:
            conditions.append(ShopOwner.user_id == filters.user_id)
        if filters.shop_id:
            conditions.append(ShopOwner.shop_id == filters.shop_id.strip())
        if filters.phone:
            conditions.append(ShopOwner.phone == filters.phone.strip())
        if filters.email:
            conditions.append(func.lower(ShopOwner.email) == filters.email.strip().lower())

        count_stmt = select(func.count(ShopOwner.id)).where(*conditions)
        total = int(self.db.scalar(count_stmt) or 0)

        stmt = (
            select(
                ShopOwner.photo,
                ShopOwner.shop_name,
                ShopOwner.user_id,
                ShopOwner.phone,
                Address.street_address,
                Address.latitude,
                Address.longitude,
                ShopOwner.geo_coordinates,
            )
            .join(Address, Address.id == ShopOwner.address_id)
            .where(*conditions)
            .order_by(ShopOwner.created_at.desc(), ShopOwner.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()

        def _safe_photo_url(photo: Any) -> str | None:
            if not photo:
                return None
            val = str(photo)
            if is_http_url(val):
                return val
            try:
                return presigned_get_url(purpose="shop_owner", key=val)
            except Exception:
                # If S3 isn't configured (e.g., boto3 not installed), don't break listing.
                return None

        items = [
            {
                "photo": row.photo,
                "photo_url": _safe_photo_url(row.photo),
                "shop_name": row.shop_name,
                "user_id": row.user_id,
                "phone": row.phone,
                "location": row.street_address,
                "geo_coordinates": row.geo_coordinates,
                "latitude": row.latitude,
                "longitude": row.longitude,
            }
            for row in rows
        ]
        return items, total

    def get_shop_id_by_email(self, email: str) -> str | None:
        normalized = (email or "").strip().lower()
        if not normalized:
            return None
        stmt = select(ShopOwner.shop_id).where(
            func.lower(ShopOwner.email) == normalized,
            ShopOwner.is_supermarket.is_(True),
            ShopOwner.is_deleted.is_(False),
        )
        return self.db.scalar(stmt)

    def get_supermarket_detail_by_user_id(self, user_id: int) -> dict[str, Any] | None:
        # IMPORTANT:
        # We avoid loading full ORM entities here because enum-mapped columns can raise
        # LookupError when DB contains values that don't match the Python Enum mapping.
        # Instead, select explicit columns and cast enums to String.

        base_stmt = (
            select(
                ShopOwner.shop_id,
                ShopOwner.user_id,
                ShopOwner.shop_name,
                ShopOwner.phone,
                ShopOwner.email,
                ShopOwner.shop_license_no,
                ShopOwner.photo,
                ShopOwner.device_token,
                cast(ShopOwner.status, String).label("status"),
                cast(ShopOwner.payment_status, String).label("payment_status"),
                ShopOwner.is_blocked,
                ShopOwner.block_reason,
                ShopOwner.geo_coordinates,
                ShopOwner.auto_assigned,
                ShopOwner.self_assigned,
                ShopOwner.is_web_app,
                ShopOwner.upi_id,
                ShopOwner.rating,
                ShopOwner.delivery_time,
                ShopOwner.contact_person_number,
                ShopOwner.contact_person_email,
                ShopOwner.is_sms_activated,
                ShopOwner.single_sms,
                ShopOwner.is_automated,
                ShopOwner.whatsapp,
                ShopOwner.task_id,
                ShopOwner.last_login_at,
                ShopOwner.created_at,
                ShopOwner.updated_at,
                ShopOwner.address_id,
                ShopOwner.subscription_id,
                Address.street_address,
                Address.city,
                Address.state,
                Address.pincode,
                Address.latitude,
                Address.longitude,
            )
            .join(Address, Address.id == ShopOwner.address_id)
            .where(
                ShopOwner.user_id == user_id,
                ShopOwner.is_supermarket.is_(True),
                ShopOwner.is_deleted.is_(False),
            )
        )
        row = self.db.execute(base_stmt).first()
        if row is None:
            return None

        shop_id = str(row.shop_id)

        subscription_row = self.db.execute(
            select(
                Subscription.subscription_id,
                Subscription.start_date,
                Subscription.end_date,
                Subscription.amount,
                cast(Subscription.status, String).label("status"),
                Subscription.last_payment_date,
            ).where(Subscription.shop_id == shop_id)
        ).first()

        promotion_row = self.db.execute(
            select(
                ShopOwnerPromotion.promotion_link,
                ShopOwnerPromotion.promotion_header,
                ShopOwnerPromotion.promotion_content,
                ShopOwnerPromotion.promotion_image_s3_key,
                ShopOwnerPromotion.is_marketing_enabled,
            ).where(ShopOwnerPromotion.shop_id == shop_id)
        ).first()

        partner_rows = self.db.execute(
            select(
                DeliveryPartner.delivery_partner_id,
                DeliveryPartner.first_name,
                DeliveryPartner.last_name,
                DeliveryPartner.phone1,
                DeliveryPartner.email,
                cast(DeliveryPartner.online_status, String).label("online_status"),
                cast(DeliveryPartner.current_status, String).label("current_status"),
                DeliveryPartner.photo,
                DeliveryPartner.vehicle_detail,
                DeliveryPartner.rating,
                DeliveryPartner.created_at,
            )
            .where(
                DeliveryPartner.shop_id == shop_id,
                DeliveryPartner.is_deleted.is_(False),
            )
            .order_by(DeliveryPartner.created_at.desc())
        ).all()

        invoice_rows = self.db.execute(
            select(
                SubscriptionInvoice.invoice_id,
                SubscriptionInvoice.invoice_number,
                SubscriptionInvoice.billing_period_start,
                SubscriptionInvoice.billing_period_end,
                SubscriptionInvoice.amount,
                cast(SubscriptionInvoice.status, String).label("status"),
                cast(SubscriptionInvoice.document_type, String).label("document_type"),
                SubscriptionInvoice.paid_at,
                SubscriptionInvoice.created_at,
            )
            .where(SubscriptionInvoice.shop_id == shop_id)
            .order_by(SubscriptionInvoice.created_at.desc())
        ).all()

        def _safe_presigned_get(key: Any) -> str | None:
            if not key:
                return None
            val = str(key)
            if is_http_url(val):
                return val
            try:
                return presigned_get_url(purpose="shop_owner", key=val)
            except Exception:
                return None

        return {
            "shop_owner": {
                "shop_id": shop_id,
                "user_id": int(row.user_id),
                "shop_name": row.shop_name,
                "phone": row.phone,
                "email": row.email,
                "shop_license_no": row.shop_license_no,
                "photo": row.photo,
                "photo_url": _safe_presigned_get(row.photo),
                "device_token": row.device_token,
                "status": row.status,
                "payment_status": row.payment_status,
                "is_blocked": bool(row.is_blocked),
                "block_reason": row.block_reason,
                "geo_coordinates": row.geo_coordinates,
                "auto_assigned": bool(row.auto_assigned),
                "self_assigned": bool(row.self_assigned),
                "is_web_app": bool(row.is_web_app),
                "upi_id": row.upi_id,
                "rating": row.rating,
                "delivery_time": row.delivery_time,
                "contact_person_number": row.contact_person_number,
                "contact_person_email": row.contact_person_email,
                "is_sms_activated": bool(row.is_sms_activated),
                "single_sms": bool(row.single_sms),
                "is_automated": bool(row.is_automated),
                "whatsapp": bool(row.whatsapp),
                "task_id": row.task_id,
                "last_login_at": row.last_login_at,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "address_id": int(row.address_id),
                "subscription_id": int(row.subscription_id) if row.subscription_id is not None else None,
            },
            "address": {
                "street_address": row.street_address,
                "city": row.city,
                "state": row.state,
                "pincode": row.pincode,
                "latitude": row.latitude,
                "longitude": row.longitude,
            },
            "subscription": (
                {
                    "subscription_id": subscription_row.subscription_id,
                    "start_date": subscription_row.start_date,
                    "end_date": subscription_row.end_date,
                    "amount": subscription_row.amount,
                    "status": subscription_row.status,
                    "last_payment_date": subscription_row.last_payment_date,
                }
                if subscription_row
                else None
            ),
            "promotion": (
                {
                    "promotion_link": promotion_row.promotion_link,
                    "promotion_header": promotion_row.promotion_header,
                    "promotion_content": promotion_row.promotion_content,
                    "promotion_image_s3_key": promotion_row.promotion_image_s3_key,
                    "promotion_image_url": _safe_presigned_get(
                        promotion_row.promotion_image_s3_key
                    ),
                    "is_marketing_enabled": promotion_row.is_marketing_enabled,
                }
                if promotion_row
                else None
            ),
            "delivery_partners": [
                {
                    "delivery_partner_id": p.delivery_partner_id,
                    "first_name": p.first_name,
                    "last_name": p.last_name,
                    "phone1": p.phone1,
                    "email": p.email,
                    "online_status": p.online_status,
                    "current_status": p.current_status,
                    "photo": p.photo,
                    "vehicle_detail": p.vehicle_detail,
                    "rating": p.rating,
                    "created_at": p.created_at,
                }
                for p in partner_rows
            ],
            "subscription_invoices": [
                {
                    "invoice_id": inv.invoice_id,
                    "invoice_number": inv.invoice_number,
                    "billing_period_start": inv.billing_period_start,
                    "billing_period_end": inv.billing_period_end,
                    "amount": inv.amount,
                    "status": inv.status,
                    "document_type": inv.document_type,
                    "paid_at": inv.paid_at,
                    "created_at": inv.created_at,
                }
                for inv in invoice_rows
            ],
            "daily_order_stats": self._daily_order_stats(shop_id),
        }

    def get_shop_activity_by_user_id(self, user_id: int, days: int) -> dict[str, Any] | None:
        shop_row = self.db.execute(
            select(ShopOwner.shop_id).where(
                ShopOwner.user_id == user_id,
                ShopOwner.is_supermarket.is_(True),
                ShopOwner.is_deleted.is_(False),
            )
        ).first()
        if shop_row is None:
            return None

        shop_id = str(shop_row.shop_id)
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=days - 1)
        previous_start = current_start - timedelta(days=days)

        grouped_rows = self.db.execute(
            select(
                func.date(Order.created_at).label("day"),
                func.count(Order.order_id).label("order_count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_amount"),
                func.sum(
                    case((cast(Order.order_status, String) == "Pending", 1), else_=0)
                ).label("pending"),
                func.sum(
                    case((cast(Order.order_status, String) == "Assigned", 1), else_=0)
                ).label("assigned"),
                func.sum(
                    case((cast(Order.order_status, String) == "Picked Up", 1), else_=0)
                ).label("picked_up"),
                func.sum(
                    case((cast(Order.order_status, String) == "Out for Delivery", 1), else_=0)
                ).label("out_for_delivery"),
                func.sum(
                    case((cast(Order.order_status, String) == "Delivered", 1), else_=0)
                ).label("delivered"),
                func.sum(
                    case(
                        (cast(Order.order_status, String) == "customer_not_available", 1),
                        else_=0,
                    )
                ).label("customer_not_available"),
                func.sum(
                    case((cast(Order.order_status, String) == "cancelled", 1), else_=0)
                ).label("cancelled"),
            )
            .where(
                Order.shop_id == shop_id,
                Order.is_deleted.is_(False),
                Order.created_at >= current_start,
                Order.created_at <= now,
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at).asc())
        ).all()

        orders_series: list[dict[str, Any]] = []
        amount_series: list[dict[str, Any]] = []
        statuses_series: list[dict[str, Any]] = []
        total_orders = 0
        total_amount = 0.0
        delivered_count = 0

        for row in grouped_rows:
            day_str = str(row.day)
            order_count = int(row.order_count or 0)
            day_amount = float(row.total_amount or 0)
            status_counts = {
                "pending": int(row.pending or 0),
                "assigned": int(row.assigned or 0),
                "picked_up": int(row.picked_up or 0),
                "out_for_delivery": int(row.out_for_delivery or 0),
                "delivered": int(row.delivered or 0),
                "customer_not_available": int(row.customer_not_available or 0),
                "cancelled": int(row.cancelled or 0),
            }

            total_orders += order_count
            total_amount += day_amount
            delivered_count += status_counts["delivered"]

            orders_series.append({"date": day_str, "count": order_count})
            amount_series.append({"date": day_str, "total_amount": round(day_amount, 2)})
            statuses_series.append({"date": day_str, "statuses": status_counts})

        previous_totals = self.db.execute(
            select(
                func.count(Order.order_id).label("order_count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_amount"),
            )
            .where(
                Order.shop_id == shop_id,
                Order.is_deleted.is_(False),
                Order.created_at >= previous_start,
                Order.created_at < current_start,
            )
        ).first()

        prev_orders = int(previous_totals.order_count or 0) if previous_totals else 0
        prev_amount = float(previous_totals.total_amount or 0) if previous_totals else 0.0

        def _growth_pct(current: float, previous: float) -> float | None:
            if previous <= 0:
                return None
            return round(((current - previous) / previous) * 100, 2)

        return {
            "shop_id": shop_id,
            "window_days": days,
            "series": {
                "orders": orders_series,
                "amount": amount_series,
                "statuses": statuses_series,
            },
            "summary": {
                "total_orders": total_orders,
                "total_amount": round(total_amount, 2),
                "avg_order_value": round(total_amount / total_orders, 2) if total_orders > 0 else 0.0,
                "delivered_rate": round((delivered_count / total_orders) * 100, 2)
                if total_orders > 0
                else 0.0,
            },
            "growth": {
                "orders_pct_vs_prev_period": _growth_pct(float(total_orders), float(prev_orders)),
                "amount_pct_vs_prev_period": _growth_pct(total_amount, prev_amount),
            },
        }

    def _daily_order_stats(self, shop_id: str) -> list[dict[str, Any]]:
        start_date = (datetime.now(timezone.utc) - timedelta(days=6)).date()
        rows = self.db.execute(
            select(
                func.date(Order.created_at).label("day"),
                cast(Order.order_status, String).label("order_status"),
                func.count(Order.order_id).label("count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
            )
            .where(
                Order.shop_id == shop_id,
                Order.is_deleted.is_(False),
                func.date(Order.created_at) >= start_date,
            )
            .group_by(func.date(Order.created_at), cast(Order.order_status, String))
            .order_by(func.date(Order.created_at).asc())
        ).all()
        daily: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = str(row.day)
            if key not in daily:
                daily[key] = {
                    "date": key,
                    "order_count": 0,
                    "total_amount": 0,
                    "status_counts": {},
                }
            daily[key]["order_count"] += int(row.count)
            daily[key]["status_counts"][str(row.order_status)] = int(row.count)
            daily[key]["total_amount"] += row.amount
        return list(daily.values())

    def get_reports_overview(self, days: int) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=days - 1)
        previous_start = current_start - timedelta(days=days)

        current = self.db.execute(
            select(
                func.count(Order.order_id).label("orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
                func.sum(case((cast(Order.order_status, String) == "Delivered", 1), else_=0)).label(
                    "delivered"
                ),
                func.sum(case((cast(Order.order_status, String) == "cancelled", 1), else_=0)).label(
                    "cancelled"
                ),
            ).where(
                Order.is_deleted.is_(False),
                Order.created_at >= current_start,
                Order.created_at <= now,
            )
        ).first()
        previous = self.db.execute(
            select(
                func.count(Order.order_id).label("orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
            ).where(
                Order.is_deleted.is_(False),
                Order.created_at >= previous_start,
                Order.created_at < current_start,
            )
        ).first()

        active_shops = int(
            self.db.scalar(
                select(func.count(ShopOwner.id)).where(
                    ShopOwner.is_supermarket.is_(True),
                    ShopOwner.is_deleted.is_(False),
                )
            )
            or 0
        )
        active_partners = int(
            self.db.scalar(
                select(func.count(DeliveryPartner.delivery_partner_id)).where(
                    DeliveryPartner.is_deleted.is_(False)
                )
            )
            or 0
        )

        trend_rows = self.db.execute(
            select(
                func.date(Order.created_at).label("day"),
                func.count(Order.order_id).label("orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
            )
            .where(
                Order.is_deleted.is_(False),
                Order.created_at >= current_start,
                Order.created_at <= now,
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at).asc())
        ).all()

        heatmap_rows = self.db.execute(
            select(
                func.extract("dow", Order.created_at).label("dow"),
                func.extract("hour", Order.created_at).label("hour"),
                func.count(Order.order_id).label("orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
            )
            .where(
                Order.is_deleted.is_(False),
                Order.created_at >= current_start,
                Order.created_at <= now,
            )
            .group_by(
                func.extract("dow", Order.created_at),
                func.extract("hour", Order.created_at),
            )
            .order_by(
                func.extract("dow", Order.created_at).asc(),
                func.extract("hour", Order.created_at).asc(),
            )
        ).all()

        shop_revenue_rows = self.db.execute(
            select(
                ShopOwner.shop_id,
                ShopOwner.shop_name,
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
                func.count(Order.order_id).label("orders"),
            )
            .join(Order, Order.shop_id == ShopOwner.shop_id)
            .where(
                ShopOwner.is_supermarket.is_(True),
                ShopOwner.is_deleted.is_(False),
                Order.is_deleted.is_(False),
                Order.created_at >= current_start,
                Order.created_at <= now,
            )
            .group_by(ShopOwner.shop_id, ShopOwner.shop_name)
            .order_by(func.coalesce(func.sum(Order.total_amount), 0).desc())
        ).all()

        current_orders = int(current.orders or 0) if current else 0
        current_amount = float(current.amount or 0) if current else 0.0
        prev_orders = int(previous.orders or 0) if previous else 0
        prev_amount = float(previous.amount or 0) if previous else 0.0

        def _pct(cur: float, prev: float) -> float | None:
            if prev <= 0:
                return None
            return round(((cur - prev) / prev) * 100, 2)

        return {
            "kpis": {
                "total_orders": current_orders,
                "total_deliveries": int(current.delivered or 0) if current else 0,
                "total_amount": round(current_amount, 2),
                "delivered_rate": round((int(current.delivered or 0) / current_orders) * 100, 2)
                if current and current_orders > 0
                else 0.0,
                "cancelled_rate": round((int(current.cancelled or 0) / current_orders) * 100, 2)
                if current and current_orders > 0
                else 0.0,
                "active_shops": active_shops,
                "active_partners": active_partners,
            },
            "growth": {
                "orders_pct_vs_prev_period": _pct(float(current_orders), float(prev_orders)),
                "amount_pct_vs_prev_period": _pct(current_amount, prev_amount),
            },
            "series": [
                {"date": str(r.day), "orders": int(r.orders or 0), "amount": round(float(r.amount or 0), 2)}
                for r in trend_rows
            ],
            "order_time_heatmap": [
                {
                    "day_of_week": int(r.dow),
                    "hour_of_day": int(r.hour),
                    "orders": int(r.orders or 0),
                    "amount": round(float(r.amount or 0), 2),
                }
                for r in heatmap_rows
            ],
            "revenue": {
                "total_revenue_all_shops": round(current_amount, 2),
                "per_shop": [
                    {
                        "shop_id": r.shop_id,
                        "shop_name": r.shop_name,
                        "orders": int(r.orders or 0),
                        "revenue": round(float(r.amount or 0), 2),
                    }
                    for r in shop_revenue_rows
                ],
            },
        }

    def get_reports_shops(self, days: int, limit: int) -> list[dict[str, Any]]:
        start = datetime.now(timezone.utc) - timedelta(days=days - 1)
        rows = self.db.execute(
            select(
                ShopOwner.shop_id,
                ShopOwner.shop_name,
                func.count(Order.order_id).label("orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
                func.sum(case((cast(Order.order_status, String) == "Delivered", 1), else_=0)).label(
                    "delivered"
                ),
                func.sum(case((cast(Order.order_status, String) == "cancelled", 1), else_=0)).label(
                    "cancelled"
                ),
            )
            .join(Order, Order.shop_id == ShopOwner.shop_id)
            .where(
                ShopOwner.is_supermarket.is_(True),
                ShopOwner.is_deleted.is_(False),
                Order.is_deleted.is_(False),
                Order.created_at >= start,
            )
            .group_by(ShopOwner.shop_id, ShopOwner.shop_name)
            .order_by(func.count(Order.order_id).desc())
            .limit(limit)
        ).all()
        payload: list[dict[str, Any]] = []
        for r in rows:
            orders = int(r.orders or 0)
            payload.append(
                {
                    "shop_id": r.shop_id,
                    "shop_name": r.shop_name,
                    "orders": orders,
                    "amount": round(float(r.amount or 0), 2),
                    "delivered_rate": round((int(r.delivered or 0) / orders) * 100, 2) if orders > 0 else 0.0,
                    "cancelled_rate": round((int(r.cancelled or 0) / orders) * 100, 2) if orders > 0 else 0.0,
                }
            )
        return payload

    def get_reports_funnel(self, days: int) -> dict[str, Any]:
        start = datetime.now(timezone.utc) - timedelta(days=days - 1)
        row = self.db.execute(
            select(
                func.sum(case((cast(Order.order_status, String) == "Pending", 1), else_=0)).label("pending"),
                func.sum(case((cast(Order.order_status, String) == "Assigned", 1), else_=0)).label("assigned"),
                func.sum(case((cast(Order.order_status, String) == "Picked Up", 1), else_=0)).label("picked_up"),
                func.sum(
                    case((cast(Order.order_status, String) == "Out for Delivery", 1), else_=0)
                ).label("out_for_delivery"),
                func.sum(case((cast(Order.order_status, String) == "Delivered", 1), else_=0)).label(
                    "delivered"
                ),
                func.sum(case((cast(Order.order_status, String) == "cancelled", 1), else_=0)).label(
                    "cancelled"
                ),
            ).where(Order.is_deleted.is_(False), Order.created_at >= start)
        ).first()
        return {
            "pending": int(row.pending or 0),
            "assigned": int(row.assigned or 0),
            "picked_up": int(row.picked_up or 0),
            "out_for_delivery": int(row.out_for_delivery or 0),
            "delivered": int(row.delivered or 0),
            "cancelled": int(row.cancelled or 0),
        }

    def get_reports_finance(self, days: int) -> dict[str, Any]:
        start = datetime.now(timezone.utc) - timedelta(days=days - 1)
        trend = self.db.execute(
            select(
                func.date(Order.created_at).label("day"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
                func.coalesce(func.sum(Order.delivery_charge), 0).label("delivery_charge"),
            )
            .where(Order.is_deleted.is_(False), Order.created_at >= start)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at).asc())
        ).all()
        payments = self.db.execute(
            select(
                cast(Order.payment_mode, String).label("payment_mode"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
            )
            .where(Order.is_deleted.is_(False), Order.created_at >= start)
            .group_by(cast(Order.payment_mode, String))
        ).all()
        return {
            "trend": [
                {
                    "date": str(r.day),
                    "amount": round(float(r.amount or 0), 2),
                    "delivery_charge": round(float(r.delivery_charge or 0), 2),
                }
                for r in trend
            ],
            "payment_split": [
                {"payment_mode": str(r.payment_mode), "amount": round(float(r.amount or 0), 2)}
                for r in payments
            ],
        }

    def create_supermarket(self, payload: SupermarketCreateRequest) -> str:
        shop_id = f"SHOP{payload.user_id}"
        if len(shop_id) > 50:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="user_id is too large to derive a valid shop_id",
                status_code=400,
                details={"max_shop_id_length": 50},
            )

        def _exists_user_id() -> bool:
            return bool(
                self.db.scalar(
                    select(func.count(ShopOwner.id)).where(ShopOwner.user_id == payload.user_id)
                )
            )

        def _exists_shop_id() -> bool:
            return bool(
                self.db.scalar(select(func.count(ShopOwner.id)).where(ShopOwner.shop_id == shop_id))
            )

        if _exists_user_id():
            raise ApiError(
                code=ErrorCode.CONFLICT,
                message="A shop owner with this user_id already exists",
                status_code=409,
                details={"field": "user_id"},
            )
        if _exists_shop_id():
            raise ApiError(
                code=ErrorCode.CONFLICT,
                message="A shop owner with this derived shop_id already exists",
                status_code=409,
                details={"field": "shop_id", "shop_id": shop_id},
            )

        shop_name = payload.shop_name.strip()
        if shop_name == "":
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="shop_name cannot be empty",
                status_code=400,
            )
        password = payload.password.strip()
        if password == "":
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="password cannot be empty",
                status_code=400,
            )

        if payload.email is not None:
            if payload.email.strip() == "":
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="email cannot be empty",
                    status_code=400,
                )
        if payload.email and payload.email.strip():
            email_norm = payload.email.strip()
            dup_email = self.db.scalar(
                select(func.count(ShopOwner.id)).where(ShopOwner.email == email_norm)
            )
            if dup_email:
                raise ApiError(
                    code=ErrorCode.CONFLICT,
                    message="email is already in use",
                    status_code=409,
                    details={"field": "email"},
                )

        if payload.shop_license_no is not None:
            if payload.shop_license_no.strip() == "":
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="shop_license_no cannot be empty",
                    status_code=400,
                )
        if payload.shop_license_no and payload.shop_license_no.strip():
            lic = payload.shop_license_no.strip()
            dup_lic = self.db.scalar(
                select(func.count(ShopOwner.id)).where(ShopOwner.shop_license_no == lic)
            )
            if dup_lic:
                raise ApiError(
                    code=ErrorCode.CONFLICT,
                    message="shop_license_no is already in use",
                    status_code=409,
                    details={"field": "shop_license_no"},
                )

        addr = payload.address
        if addr.street_address.strip() == "":
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="street_address cannot be empty",
                status_code=400,
            )
        if addr.city.strip() == "":
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="city cannot be empty",
                status_code=400,
            )
        if addr.state.strip() == "":
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="state cannot be empty",
                status_code=400,
            )
        if addr.pincode.strip() == "":
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="pincode cannot be empty",
                status_code=400,
            )
        address = Address(
            street_address=addr.street_address.strip(),
            city=addr.city.strip(),
            state=addr.state.strip(),
            pincode=addr.pincode.strip(),
            latitude=addr.latitude,
            longitude=addr.longitude,
        )
        self.db.add(address)
        self.db.flush()

        shop_owner = ShopOwner(
            shop_id=shop_id,
            user_id=payload.user_id,
            shop_name=shop_name,
            password=password,
            phone=payload.phone.strip() if payload.phone and payload.phone.strip() else None,
            email=payload.email.strip() if payload.email and payload.email.strip() else None,
            shop_license_no=(
                payload.shop_license_no.strip()
                if payload.shop_license_no and payload.shop_license_no.strip()
                else None
            ),
            photo=payload.photo,
            address_id=address.id,
            geo_coordinates=payload.geo_coordinates,
            upi_id=payload.upi_id,
            delivery_time=payload.delivery_time if payload.delivery_time is not None else 30,
            is_supermarket=True,
            # DB enum expects lowercase values (e.g. "active"), not Enum names (e.g. "ACTIVE").
            status=ShopStatus.ACTIVE.value,
            payment_status=ShopPaymentStatus.PENDING.value,
        )
        self.db.add(shop_owner)
        self.db.flush()

        if payload.subscription is not None:
            # Some clients may send an incomplete subscription payload.
            # If any required subscription fields are missing, ignore it.
            subscription_complete = (
                payload.subscription.start_date is not None
                and payload.subscription.end_date is not None
                and payload.subscription.amount is not None
            )
            if not subscription_complete:
                pass
            else:
                sub = Subscription(
                    shop_id=shop_id,
                    start_date=payload.subscription.start_date,
                    end_date=payload.subscription.end_date,
                    amount=payload.subscription.amount,
                    status=payload.subscription.status.value
                    if isinstance(payload.subscription.status, SubscriptionStatus)
                    else str(payload.subscription.status),
                )
                self.db.add(sub)
                self.db.flush()
                shop_owner.subscription_id = sub.subscription_id

        if payload.promotion is not None:
            promo = payload.promotion
            self.db.add(
                ShopOwnerPromotion(
                    shop_id=shop_id,
                    promotion_link=promo.promotion_link,
                    promotion_header=promo.promotion_header,
                    promotion_content=promo.promotion_content,
                    promotion_image_s3_key=promo.promotion_image_s3_key,
                    is_marketing_enabled=promo.is_marketing_enabled,
                )
            )

        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise ApiError(
                code=ErrorCode.CONFLICT,
                message="Could not create supermarket due to a data conflict",
                status_code=409,
            ) from exc

        return shop_id

    def update_supermarket(self, user_id: int, payload: SupermarketUpdateRequest) -> None:
        shop_owner = self.db.scalar(
            select(ShopOwner).where(
                ShopOwner.user_id == user_id,
                ShopOwner.is_supermarket.is_(True),
                ShopOwner.is_deleted.is_(False),
            )
        )
        if shop_owner is None:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Supermarket not found",
                status_code=404,
            )

        patch = payload.model_dump(exclude_unset=True)

        # Normalize enum objects to DB enum values (lowercase strings).
        if "status" in patch and patch["status"] is not None:
            if isinstance(patch["status"], ShopStatus):
                patch["status"] = patch["status"].value
            else:
                patch["status"] = str(patch["status"])
        if "payment_status" in patch and patch["payment_status"] is not None:
            if isinstance(patch["payment_status"], ShopPaymentStatus):
                patch["payment_status"] = patch["payment_status"].value
            else:
                patch["payment_status"] = str(patch["payment_status"])

        # Nested address update (if provided)
        address_patch = patch.pop("address", None)
        if address_patch is not None:
            address = self.db.get(Address, shop_owner.address_id)
            if address is None:
                raise ApiError(
                    code=ErrorCode.INTERNAL_SERVER_ERROR,
                    message="Supermarket address is missing",
                    status_code=500,
                )
            for key, value in address_patch.items():
                if value is None:
                    continue
                if isinstance(value, str):
                    value = value.strip()
                    if value == "":
                        raise ApiError(
                            code=ErrorCode.VALIDATION_ERROR,
                            message=f"{key} cannot be empty",
                            status_code=400,
                        )
                setattr(address, key, value)
            self.db.add(address)

        # Normalize strings for uniqueness checks
        if "email" in patch and patch["email"] is not None:
            patch["email"] = patch["email"].strip()
            if patch["email"] == "":
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="email cannot be empty",
                    status_code=400,
                )
        if "shop_license_no" in patch and patch["shop_license_no"] is not None:
            patch["shop_license_no"] = patch["shop_license_no"].strip()
            if patch["shop_license_no"] == "":
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="shop_license_no cannot be empty",
                    status_code=400,
                )
        if "phone" in patch and patch["phone"] is not None:
            patch["phone"] = patch["phone"].strip()
            if patch["phone"] == "":
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="phone cannot be empty",
                    status_code=400,
                )
        if "shop_name" in patch and patch["shop_name"] is not None:
            patch["shop_name"] = patch["shop_name"].strip()
            if patch["shop_name"] == "":
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="shop_name cannot be empty",
                    status_code=400,
                )

        # Uniqueness checks (exclude current shop owner)
        if "email" in patch and patch["email"] is not None:
            dup_email = self.db.scalar(
                select(func.count(ShopOwner.id)).where(
                    ShopOwner.email == patch["email"],
                    ShopOwner.user_id != user_id,
                )
            )
            if dup_email:
                raise ApiError(
                    code=ErrorCode.CONFLICT,
                    message="email is already in use",
                    status_code=409,
                    details={"field": "email"},
                )

        if "shop_license_no" in patch and patch["shop_license_no"] is not None:
            dup_lic = self.db.scalar(
                select(func.count(ShopOwner.id)).where(
                    ShopOwner.shop_license_no == patch["shop_license_no"],
                    ShopOwner.user_id != user_id,
                )
            )
            if dup_lic:
                raise ApiError(
                    code=ErrorCode.CONFLICT,
                    message="shop_license_no is already in use",
                    status_code=409,
                    details={"field": "shop_license_no"},
                )

        for key, value in patch.items():
            if value is not None:
                setattr(shop_owner, key, value)

        self.db.add(shop_owner)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise ApiError(
                code=ErrorCode.CONFLICT,
                message="Could not update supermarket due to a data conflict",
                status_code=409,
            ) from exc

    def soft_delete_supermarket(self, user_id: int) -> None:
        shop_owner = self.db.scalar(
            select(ShopOwner).where(
                ShopOwner.user_id == user_id,
                ShopOwner.is_supermarket.is_(True),
                ShopOwner.is_deleted.is_(False),
            )
        )
        if shop_owner is None:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Supermarket not found",
                status_code=404,
            )

        shop_owner.is_deleted = True
        self.db.add(shop_owner)

        # Also soft-delete delivery partners for this shop.
        self.db.execute(
            update(DeliveryPartner)
            .where(
                DeliveryPartner.shop_id == shop_owner.shop_id,
                DeliveryPartner.is_deleted.is_(False),
            )
            .values(is_deleted=True)
        )

        self.db.flush()

