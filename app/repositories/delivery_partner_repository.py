from __future__ import annotations

from typing import Any

from sqlalchemy import String, cast, func, select, update
from sqlalchemy.orm import Session

from app.api.v1.schemas.delivery_partner import DeliveryPartnerListFilters
from app.domain.repositories.delivery_partner_repository import AbstractDeliveryPartnerRepository
from app.infrastructure.db.models.delivery_partner import DeliveryPartner
from app.infrastructure.db.models.shop_owner import ShopOwner
from app.infrastructure.storage.s3 import is_http_url, presigned_get_url


class DeliveryPartnerRepository(AbstractDeliveryPartnerRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_delivery_partners(
        self, page: int, limit: int, filters: DeliveryPartnerListFilters
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = []
        if not bool(getattr(filters, "include_deleted", False)):
            conditions.append(DeliveryPartner.is_deleted.is_(False))

        if filters.delivery_partner_id:
            conditions.append(
                DeliveryPartner.delivery_partner_id == filters.delivery_partner_id.strip()
            )

        if filters.shop_id:
            conditions.append(DeliveryPartner.shop_id == filters.shop_id.strip())

        if filters.shop_name:
            shop_name_norm = filters.shop_name.strip()
            if shop_name_norm:
                conditions.append(ShopOwner.shop_name.ilike(f"%{shop_name_norm}%"))

        if filters.phone:
            phone_norm = filters.phone.strip()
            if phone_norm.isdigit():
                conditions.append(DeliveryPartner.phone1 == int(phone_norm))
            else:
                # If client includes '+' etc., ignore filter rather than erroring here.
                pass

        if filters.name:
            name_norm = filters.name.strip()
            if name_norm:
                conditions.append(
                    func.concat(
                        func.coalesce(DeliveryPartner.first_name, ""),
                        " ",
                        func.coalesce(DeliveryPartner.last_name, ""),
                    ).ilike(f"%{name_norm}%")
                )

        if filters.current_status:
            status_norm = filters.current_status.strip()
            if status_norm:
                conditions.append(cast(DeliveryPartner.current_status, String) == status_norm)

        if filters.online_status:
            online_norm = filters.online_status.strip()
            if online_norm:
                conditions.append(cast(DeliveryPartner.online_status, String) == online_norm)

        count_stmt = (
            select(func.count(DeliveryPartner.delivery_partner_id))
            .select_from(DeliveryPartner)
            .join(ShopOwner, ShopOwner.shop_id == DeliveryPartner.shop_id)
            .where(*conditions)
        )
        total = int(self.db.scalar(count_stmt) or 0)

        stmt = (
            select(
                DeliveryPartner.delivery_partner_id,
                DeliveryPartner.shop_id,
                ShopOwner.shop_name,
                DeliveryPartner.first_name,
                DeliveryPartner.last_name,
                DeliveryPartner.phone1,
                DeliveryPartner.photo,
                DeliveryPartner.is_deleted,
                DeliveryPartner.created_at,
            )
            .join(ShopOwner, ShopOwner.shop_id == DeliveryPartner.shop_id)
            .where(*conditions)
            .order_by(DeliveryPartner.created_at.desc())
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
                return presigned_get_url(purpose="delivery_partner", key=val)
            except Exception:
                return None

        items: list[dict[str, Any]] = []
        for r in rows:
            full_name = " ".join([p for p in [r.first_name, r.last_name] if p]).strip()
            items.append(
                {
                    "delivery_partner_id": r.delivery_partner_id,
                    "shop_id": r.shop_id,
                    "shop_name": r.shop_name,
                    "name": full_name or r.first_name,
                    "phone": str(r.phone1),
                    "photo": r.photo,
                    "photo_url": _safe_photo_url(r.photo),
                    "is_deleted": bool(r.is_deleted),
                }
            )

        return items, total

    def get_delivery_partner_detail(self, delivery_partner_id: str) -> dict[str, Any] | None:
        stmt = (
            select(
                DeliveryPartner.delivery_partner_id,
                DeliveryPartner.shop_id,
                ShopOwner.shop_name,
                DeliveryPartner.first_name,
                DeliveryPartner.last_name,
                DeliveryPartner.license_no,
                DeliveryPartner.license_image,
                DeliveryPartner.govt_id_image,
                DeliveryPartner.join_date,
                DeliveryPartner.is_blocked,
                cast(DeliveryPartner.current_status, String).label("current_status"),
                DeliveryPartner.order_count,
                DeliveryPartner.age,
                DeliveryPartner.phone1,
                DeliveryPartner.phone2,
                DeliveryPartner.email,
                cast(DeliveryPartner.online_status, String).label("online_status"),
                DeliveryPartner.rating,
                DeliveryPartner.photo,
                DeliveryPartner.device_token,
                DeliveryPartner.device_id,
                DeliveryPartner.last_login,
                DeliveryPartner.last_order,
                DeliveryPartner.vehicle_detail,
                DeliveryPartner.total_bonus,
                DeliveryPartner.total_penalty,
                DeliveryPartner.liquid_cash,
                DeliveryPartner.created_at,
                DeliveryPartner.updated_at,
                DeliveryPartner.is_deleted,
            )
            .join(ShopOwner, ShopOwner.shop_id == DeliveryPartner.shop_id)
            .where(
                DeliveryPartner.delivery_partner_id == delivery_partner_id,
                DeliveryPartner.is_deleted.is_(False),
            )
        )
        r = self.db.execute(stmt).first()
        if r is None:
            return None

        def _safe_photo_url(photo: Any) -> str | None:
            if not photo:
                return None
            val = str(photo)
            if is_http_url(val):
                return val
            try:
                return presigned_get_url(purpose="delivery_partner", key=val)
            except Exception:
                return None

        return {
            "delivery_partner_id": r.delivery_partner_id,
            "shop_id": r.shop_id,
            "shop_name": r.shop_name,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "license_no": r.license_no,
            "license_image": r.license_image,
            "govt_id_image": r.govt_id_image,
            "join_date": r.join_date,
            "is_blocked": bool(r.is_blocked),
            "current_status": r.current_status,
            "order_count": int(r.order_count),
            "age": int(r.age),
            "phone1": str(r.phone1),
            "phone2": str(r.phone2) if r.phone2 is not None else None,
            "email": r.email,
            "online_status": r.online_status,
            "rating": r.rating,
            "photo": r.photo,
            "photo_url": _safe_photo_url(r.photo),
            "device_token": r.device_token,
            "device_id": r.device_id,
            "last_login": r.last_login,
            "last_order": r.last_order,
            "vehicle_detail": r.vehicle_detail,
            "total_bonus": int(r.total_bonus),
            "total_penalty": int(r.total_penalty),
            "liquid_cash": r.liquid_cash,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "is_deleted": bool(r.is_deleted),
        }

    def set_delivery_partner_blocked(self, delivery_partner_id: str, *, blocked: bool) -> bool:
        result = self.db.execute(
            update(DeliveryPartner)
            .where(
                DeliveryPartner.delivery_partner_id == delivery_partner_id,
                DeliveryPartner.is_deleted.is_(False),
            )
            .values(is_blocked=bool(blocked))
        )
        if result.rowcount == 0:
            self.db.rollback()
            return False
        self.db.commit()
        return True

    def soft_delete_delivery_partner(self, delivery_partner_id: str) -> bool:
        result = self.db.execute(
            update(DeliveryPartner)
            .where(
                DeliveryPartner.delivery_partner_id == delivery_partner_id,
                DeliveryPartner.is_deleted.is_(False),
            )
            .values(is_deleted=True)
        )
        if result.rowcount == 0:
            self.db.rollback()
            return False
        self.db.commit()
        return True

    def restore_delivery_partner(self, delivery_partner_id: str) -> bool:
        result = self.db.execute(
            update(DeliveryPartner)
            .where(
                DeliveryPartner.delivery_partner_id == delivery_partner_id,
                DeliveryPartner.is_deleted.is_(True),
            )
            .values(is_deleted=False)
        )
        if result.rowcount == 0:
            self.db.rollback()
            return False
        self.db.commit()
        return True

