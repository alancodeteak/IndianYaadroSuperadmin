from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.schemas.shop_owner import SupermarketListFilters
from app.domain.repositories.shop_owner_repository import AbstractShopOwnerRepository
from app.infrastructure.db.models.address import Address
from app.infrastructure.db.models.delivery_partner import DeliveryPartner
from app.infrastructure.db.models.order import Order
from app.infrastructure.db.models.shop_owner import ShopOwner
from app.infrastructure.db.models.shop_owner_promotion import ShopOwnerPromotion
from app.infrastructure.db.models.subscription import Subscription
from app.infrastructure.db.models.subscription_invoice import SubscriptionInvoice


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
        items = [
            {
                "photo": row.photo,
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

    def get_supermarket_detail_by_user_id(self, user_id: int) -> dict[str, Any] | None:
        base_stmt = (
            select(
                ShopOwner,
                Address,
            )
            .join(Address, Address.id == ShopOwner.address_id)
            .where(
                ShopOwner.user_id == user_id,
                ShopOwner.is_supermarket.is_(True),
                ShopOwner.is_deleted.is_(False),
            )
        )
        base_row = self.db.execute(base_stmt).first()
        if base_row is None:
            return None

        shop_owner: ShopOwner = base_row[0]
        address: Address = base_row[1]

        subscription = self.db.scalar(
            select(Subscription).where(Subscription.shop_id == shop_owner.shop_id)
        )
        promotion = self.db.scalar(
            select(ShopOwnerPromotion).where(ShopOwnerPromotion.shop_id == shop_owner.shop_id)
        )
        partners = list(
            self.db.scalars(
                select(DeliveryPartner)
                .where(
                    DeliveryPartner.shop_id == shop_owner.shop_id,
                    DeliveryPartner.is_deleted.is_(False),
                )
                .order_by(DeliveryPartner.created_at.desc())
            ).all()
        )
        invoices = list(
            self.db.scalars(
                select(SubscriptionInvoice)
                .where(SubscriptionInvoice.shop_id == shop_owner.shop_id)
                .order_by(SubscriptionInvoice.created_at.desc())
            ).all()
        )

        return {
            "shop_owner": {
                "shop_id": shop_owner.shop_id,
                "user_id": shop_owner.user_id,
                "shop_name": shop_owner.shop_name,
                "phone": shop_owner.phone,
                "email": shop_owner.email,
                "photo": shop_owner.photo,
                "status": str(shop_owner.status),
                "payment_status": str(shop_owner.payment_status),
                "is_blocked": shop_owner.is_blocked,
                "geo_coordinates": shop_owner.geo_coordinates,
                "upi_id": shop_owner.upi_id,
                "rating": shop_owner.rating,
                "delivery_time": shop_owner.delivery_time,
                "created_at": shop_owner.created_at,
                "updated_at": shop_owner.updated_at,
            },
            "address": {
                "street_address": address.street_address,
                "city": address.city,
                "state": address.state,
                "pincode": address.pincode,
                "latitude": address.latitude,
                "longitude": address.longitude,
            },
            "subscription": (
                {
                    "subscription_id": subscription.subscription_id,
                    "start_date": subscription.start_date,
                    "end_date": subscription.end_date,
                    "amount": subscription.amount,
                    "status": str(subscription.status),
                    "last_payment_date": subscription.last_payment_date,
                }
                if subscription
                else None
            ),
            "promotion": (
                {
                    "promotion_link": promotion.promotion_link,
                    "promotion_header": promotion.promotion_header,
                    "promotion_content": promotion.promotion_content,
                    "promotion_image_s3_key": promotion.promotion_image_s3_key,
                    "is_marketing_enabled": promotion.is_marketing_enabled,
                }
                if promotion
                else None
            ),
            "delivery_partners": [
                {
                    "delivery_partner_id": partner.delivery_partner_id,
                    "first_name": partner.first_name,
                    "last_name": partner.last_name,
                    "phone1": partner.phone1,
                    "email": partner.email,
                    "online_status": str(partner.online_status),
                    "current_status": str(partner.current_status),
                    "photo": partner.photo,
                    "vehicle_detail": partner.vehicle_detail,
                    "rating": partner.rating,
                    "created_at": partner.created_at,
                }
                for partner in partners
            ],
            "subscription_invoices": [
                {
                    "invoice_id": inv.invoice_id,
                    "invoice_number": inv.invoice_number,
                    "billing_period_start": inv.billing_period_start,
                    "billing_period_end": inv.billing_period_end,
                    "amount": inv.amount,
                    "status": str(inv.status),
                    "document_type": str(inv.document_type),
                    "paid_at": inv.paid_at,
                    "created_at": inv.created_at,
                }
                for inv in invoices
            ],
            "daily_order_stats": self._daily_order_stats(shop_owner.shop_id),
        }

    def _daily_order_stats(self, shop_id: str) -> list[dict[str, Any]]:
        start_date = (datetime.now(timezone.utc) - timedelta(days=6)).date()
        rows = self.db.execute(
            select(
                func.date(Order.created_at).label("day"),
                Order.order_status,
                func.count(Order.order_id).label("count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
            )
            .where(
                Order.shop_id == shop_id,
                Order.is_deleted.is_(False),
                func.date(Order.created_at) >= start_date,
            )
            .group_by(func.date(Order.created_at), Order.order_status)
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

