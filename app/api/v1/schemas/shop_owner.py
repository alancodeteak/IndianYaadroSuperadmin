from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.infrastructure.db.models.enums import ShopPaymentStatus, ShopStatus


class ShopOwnerBase(BaseModel):
    shop_id: str
    user_id: int
    shop_name: str
    phone: str | None = None
    email: str | None = None
    shop_license_no: str | None = None
    photo: str | None = None
    address_id: int
    status: ShopStatus = ShopStatus.ACTIVE
    is_blocked: bool = False
    is_deleted: bool = False
    payment_status: ShopPaymentStatus = ShopPaymentStatus.PENDING
    rating: Decimal | None = None
    geo_coordinates: dict[str, Any] | None = None
    is_supermarket: bool = True
    hmac_secret: str | None = None
    upi_id: str | None = None
    delivery_time: int | None = 30


class ShopOwnerCreate(ShopOwnerBase):
    password: str


class ShopOwnerUpdate(BaseModel):
    shop_name: str | None = None
    password: str | None = None
    phone: str | None = None
    email: str | None = None
    shop_license_no: str | None = None
    photo: str | None = None
    address_id: int | None = None
    status: ShopStatus | None = None
    is_blocked: bool | None = None
    is_deleted: bool | None = None
    payment_status: ShopPaymentStatus | None = None
    rating: Decimal | None = None
    geo_coordinates: dict[str, Any] | None = None
    is_supermarket: bool | None = None
    hmac_secret: str | None = None
    upi_id: str | None = None
    delivery_time: int | None = None


class ShopOwnerRead(ShopOwnerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int | None = None
    device_token: str | None = None
    contact_person_number: str | None = None
    contact_person_email: str | None = None
    is_sms_activated: bool = False
    single_sms: bool = False
    is_automated: bool = False
    whatsapp: bool = False
    block_reason: str | None = None
    task_id: str | None = None
    is_web_app: bool = True
    auto_assigned: bool = False
    self_assigned: bool = False
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ShopOwnerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shop_id: str
    user_id: int
    shop_name: str
    phone: str | None = None
    status: ShopStatus
    payment_status: ShopPaymentStatus
    is_blocked: bool
    is_deleted: bool


class SupermarketListItem(BaseModel):
    photo: str | None = None
    shop_name: str
    user_id: int
    phone: str | None = None
    location: str
    geo_coordinates: dict[str, Any] | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class SupermarketListMeta(BaseModel):
    currentPage: int
    limit: int
    total: int
    totalPages: int

