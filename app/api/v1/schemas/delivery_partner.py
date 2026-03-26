from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.infrastructure.db.models.enums import DeliveryOnlineStatus, DeliveryPartnerStatus


class DeliveryPartnerBase(BaseModel):
    delivery_partner_id: str
    shop_id: str
    first_name: str
    last_name: str | None = None
    license_no: str
    license_image: str
    govt_id_image: str | None = None
    age: int
    phone1: int
    phone2: int | None = None
    email: str | None = None
    current_status: DeliveryPartnerStatus = DeliveryPartnerStatus.IDLE
    online_status: DeliveryOnlineStatus = DeliveryOnlineStatus.OFFLINE
    is_blocked: bool = False
    is_deleted: bool = False
    order_count: int = 0
    rating: Decimal | None = None
    photo: str
    liquid_cash: Decimal = Decimal("0")
    hmac_secret: str | None = None


class DeliveryPartnerCreate(DeliveryPartnerBase):
    password: str


class DeliveryPartnerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    license_no: str | None = None
    license_image: str | None = None
    govt_id_image: str | None = None
    age: int | None = None
    phone1: int | None = None
    phone2: int | None = None
    email: str | None = None
    current_status: DeliveryPartnerStatus | None = None
    online_status: DeliveryOnlineStatus | None = None
    is_blocked: bool | None = None
    is_deleted: bool | None = None
    order_count: int | None = None
    rating: Decimal | None = None
    photo: str | None = None
    device_token: str | None = None
    device_id: str | None = None
    vehicle_detail: str | None = None
    liquid_cash: Decimal | None = None
    hmac_secret: str | None = None


class DeliveryPartnerRead(DeliveryPartnerBase):
    model_config = ConfigDict(from_attributes=True)

    device_token: str | None = None
    device_id: str | None = None
    join_date: datetime
    last_login: datetime | None = None
    last_order: datetime | None = None
    vehicle_detail: str | None = None
    total_bonus: int
    total_penalty: int
    created_at: datetime
    updated_at: datetime


class DeliveryPartnerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    delivery_partner_id: str
    shop_id: str
    first_name: str
    last_name: str | None = None
    phone1: int
    current_status: DeliveryPartnerStatus
    online_status: DeliveryOnlineStatus
    is_blocked: bool
    is_deleted: bool


class DeliveryPartnerListFilters(BaseModel):
    name: str | None = None
    shop_id: str | None = None
    phone: str | None = None
    delivery_partner_id: str | None = None
    shop_name: str | None = None
    current_status: str | None = None
    online_status: str | None = None


class DeliveryPartnerCard(BaseModel):
    delivery_partner_id: str
    shop_id: str
    shop_name: str | None = None
    name: str
    phone: str
    photo: str | None = None
    photo_url: str | None = None


class DeliveryPartnerDetail(BaseModel):
    delivery_partner_id: str
    shop_id: str
    shop_name: str | None = None
    first_name: str
    last_name: str | None = None
    license_no: str
    license_image: str
    govt_id_image: str | None = None
    join_date: datetime
    is_blocked: bool
    current_status: str
    order_count: int
    age: int
    phone1: str
    phone2: str | None = None
    email: str | None = None
    online_status: str
    rating: Decimal | None = None
    photo: str
    photo_url: str | None = None
    device_token: str | None = None
    device_id: str | None = None
    last_login: datetime | None = None
    last_order: datetime | None = None
    vehicle_detail: str | None = None
    total_bonus: int
    total_penalty: int
    liquid_cash: Decimal
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class DeliveryPartnerBlockRequest(BaseModel):
    blocked: bool


class DeliveryPartnerBlockResponse(BaseModel):
    delivery_partner_id: str
    is_blocked: bool


class DeliveryPartnerDeleteResponse(BaseModel):
    delivery_partner_id: str
    deleted: bool

