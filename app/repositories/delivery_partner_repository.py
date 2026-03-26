from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
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
        conditions = [DeliveryPartner.is_deleted.is_(False)]

        if filters.shop_id:
            conditions.append(DeliveryPartner.shop_id == filters.shop_id.strip())

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

        count_stmt = select(func.count(DeliveryPartner.delivery_partner_id)).where(*conditions)
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
                }
            )

        return items, total

