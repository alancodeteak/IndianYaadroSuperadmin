from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, update
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
                code=ErrorCode.VALIDATION_ERROR,
                message="A shop owner with this user_id already exists",
                status_code=409,
                details={"field": "user_id"},
            )
        if _exists_shop_id():
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="A shop owner with this derived shop_id already exists",
                status_code=409,
                details={"field": "shop_id", "shop_id": shop_id},
            )

        if payload.email and payload.email.strip():
            email_norm = payload.email.strip()
            dup_email = self.db.scalar(
                select(func.count(ShopOwner.id)).where(ShopOwner.email == email_norm)
            )
            if dup_email:
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="email is already in use",
                    status_code=409,
                    details={"field": "email"},
                )

        if payload.shop_license_no and payload.shop_license_no.strip():
            lic = payload.shop_license_no.strip()
            dup_lic = self.db.scalar(
                select(func.count(ShopOwner.id)).where(ShopOwner.shop_license_no == lic)
            )
            if dup_lic:
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="shop_license_no is already in use",
                    status_code=409,
                    details={"field": "shop_license_no"},
                )

        addr = payload.address
        address = Address(
            street_address=addr.street_address,
            city=addr.city,
            state=addr.state,
            pincode=addr.pincode,
            latitude=addr.latitude,
            longitude=addr.longitude,
        )
        self.db.add(address)
        self.db.flush()

        shop_owner = ShopOwner(
            shop_id=shop_id,
            user_id=payload.user_id,
            shop_name=payload.shop_name,
            password=payload.password,
            phone=payload.phone,
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
                    status=payload.subscription.status,
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
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
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
                if value is not None:
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
                    code=ErrorCode.VALIDATION_ERROR,
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
                    code=ErrorCode.VALIDATION_ERROR,
                    message="shop_license_no is already in use",
                    status_code=409,
                    details={"field": "shop_license_no"},
                )

        for key, value in patch.items():
            if value is not None:
                setattr(shop_owner, key, value)

        self.db.add(shop_owner)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
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

        self.db.commit()

