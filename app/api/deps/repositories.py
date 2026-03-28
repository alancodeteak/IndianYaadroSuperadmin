from fastapi import Depends
from sqlalchemy.orm import Session

# Per-request session; never cache on a repository or singleton.
from app.infrastructure.db.session import get_db_session
from app.repositories.delivery_partner_repository import DeliveryPartnerRepository
from app.repositories.daily_activity_repository import DailyActivityRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.sales_activity_repository import SalesActivityRepository
from app.repositories.shop_owner_repository import ShopOwnerRepository


def get_order_repository(db: Session = Depends(get_db_session)) -> OrderRepository:
    return OrderRepository(db=db)


def get_shop_owner_repository(db: Session = Depends(get_db_session)) -> ShopOwnerRepository:
    return ShopOwnerRepository(db=db)


def get_delivery_partner_repository(
    db: Session = Depends(get_db_session),
) -> DeliveryPartnerRepository:
    return DeliveryPartnerRepository(db=db)


def get_invoice_repository(db: Session = Depends(get_db_session)) -> InvoiceRepository:
    return InvoiceRepository(db=db)


def get_daily_activity_repository(db: Session = Depends(get_db_session)) -> DailyActivityRepository:
    return DailyActivityRepository(db=db)


def get_sales_activity_repository(db: Session = Depends(get_db_session)) -> SalesActivityRepository:
    return SalesActivityRepository(db=db)

