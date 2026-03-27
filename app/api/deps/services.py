from fastapi import Depends

from app.api.core.config import get_settings
from app.api.deps.otp import get_otp_notifier, get_otp_store
from app.api.deps.repositories import (
    get_daily_activity_repository,
    get_delivery_partner_repository,
    get_invoice_repository,
    get_order_repository,
    get_sales_activity_repository,
    get_shop_owner_repository,
)
from app.api.deps.session import get_session_service
from app.repositories.delivery_partner_repository import DeliveryPartnerRepository
from app.repositories.daily_activity_repository import DailyActivityRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.sales_activity_repository import SalesActivityRepository
from app.repositories.shop_owner_repository import ShopOwnerRepository
from app.services.auth_service import AuthService
from app.services.daily_activity_service import DailyActivityService
from app.services.invoice_service import InvoiceService
from app.services.sales_activity_service import SalesActivityService
from app.services.order_service import OrderService
from app.services.delivery_partner_service import DeliveryPartnerService
from app.services.shop_owner_service import ShopOwnerService


def get_order_service(repo: OrderRepository = Depends(get_order_repository)) -> OrderService:
    return OrderService(repository=repo)


def get_shop_owner_service(
    repo: ShopOwnerRepository = Depends(get_shop_owner_repository),
) -> ShopOwnerService:
    return ShopOwnerService(repository=repo)


def get_delivery_partner_service(
    repo: DeliveryPartnerRepository = Depends(get_delivery_partner_repository),
) -> DeliveryPartnerService:
    return DeliveryPartnerService(repository=repo)


def get_invoice_service(
    repo: InvoiceRepository = Depends(get_invoice_repository),
) -> InvoiceService:
    return InvoiceService(repository=repo)


def get_daily_activity_service(
    repo: DailyActivityRepository = Depends(get_daily_activity_repository),
) -> DailyActivityService:
    return DailyActivityService(repository=repo)


def get_sales_activity_service(
    repo: SalesActivityRepository = Depends(get_sales_activity_repository),
) -> SalesActivityService:
    return SalesActivityService(repository=repo)


def get_auth_service() -> AuthService:
    return AuthService(
        settings=get_settings(),
        otp_store=get_otp_store(),
        otp_notifier=get_otp_notifier(),
        session_service=get_session_service(),
    )

