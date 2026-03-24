from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.repositories.shop_owner_repository import AbstractShopOwnerRepository
from app.infrastructure.db.models.address import Address
from app.infrastructure.db.models.shop_owner import ShopOwner


class ShopOwnerRepository(AbstractShopOwnerRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_supermarkets(self, page: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        count_stmt = select(func.count(ShopOwner.id)).where(
            ShopOwner.is_supermarket.is_(True),
            ShopOwner.is_deleted.is_(False),
        )
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
            .where(
                ShopOwner.is_supermarket.is_(True),
                ShopOwner.is_deleted.is_(False),
            )
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

