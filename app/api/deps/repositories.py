from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db_session
from app.repositories.delivery_partner_repository import DeliveryPartnerRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.shop_owner_repository import ShopOwnerRepository


def get_order_repository(db: Session = Depends(get_db_session)) -> OrderRepository:
    return OrderRepository(db=db)


def get_shop_owner_repository(db: Session = Depends(get_db_session)) -> ShopOwnerRepository:
    return ShopOwnerRepository(db=db)


def get_delivery_partner_repository(
    db: Session = Depends(get_db_session),
) -> DeliveryPartnerRepository:
    return DeliveryPartnerRepository(db=db)

