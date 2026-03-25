from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import String, cast, func, select, update
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
                ShopOwner.photo,
                cast(ShopOwner.status, String).label("status"),
                cast(ShopOwner.payment_status, String).label("payment_status"),
                ShopOwner.is_blocked,
                ShopOwner.geo_coordinates,
                ShopOwner.upi_id,
                ShopOwner.rating,
                ShopOwner.delivery_time,
                ShopOwner.created_at,
                ShopOwner.updated_at,
                ShopOwner.address_id,
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

        return {
            "shop_owner": {
                "shop_id": shop_id,
                "user_id": int(row.user_id),
                "shop_name": row.shop_name,
                "phone": row.phone,
                "email": row.email,
                "photo": row.photo,
                "status": row.status,
                "payment_status": row.payment_status,
                "is_blocked": bool(row.is_blocked),
                "geo_coordinates": row.geo_coordinates,
                "upi_id": row.upi_id,
                "rating": row.rating,
                "delivery_time": row.delivery_time,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
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
            self.db.commit()
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

        self.db.commit()

