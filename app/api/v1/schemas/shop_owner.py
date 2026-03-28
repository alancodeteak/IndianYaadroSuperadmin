from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.infrastructure.db.models.enums import (
    ShopPaymentStatus,
    ShopStatus,
    SubscriptionStatus,
)


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


class SupermarketListFilters(BaseModel):
    name: str | None = None
    user_id: int | None = None
    shop_id: str | None = None
    phone: str | None = None
    email: str | None = None


class SupermarketCreateAddress(BaseModel):
    street_address: str = Field(min_length=1, max_length=250)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=1, max_length=20)
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class SupermarketCreateSubscription(BaseModel):
    # Subscription is optional at the supermarket level, but some clients may send an
    # incomplete `subscription` object. We allow partial payloads and decide in the
    # repository whether to create the subscription or ignore it.
    start_date: datetime | None = None
    end_date: datetime | None = None
    amount: Decimal | None = None
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    @model_validator(mode="after")
    def end_after_start(self) -> "SupermarketCreateSubscription":
        if self.start_date is not None and self.end_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError("end_date must be after start_date")
        return self


class SupermarketCreatePromotion(BaseModel):
    promotion_link: str | None = Field(default=None, max_length=512)
    promotion_header: str | None = Field(default=None, max_length=255)
    promotion_content: str | None = None
    promotion_image_s3_key: str | None = Field(default=None, max_length=512)
    is_marketing_enabled: bool = False


class SupermarketCreateRequest(BaseModel):
    user_id: int = Field(gt=0)
    shop_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=255)
    address: SupermarketCreateAddress
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=100)
    shop_license_no: str | None = Field(default=None, max_length=100)
    photo: str | None = Field(default=None, max_length=255)
    geo_coordinates: dict[str, Any] | None = None
    upi_id: str | None = Field(default=None, max_length=100)
    delivery_time: int | None = Field(default=None, ge=0)
    subscription: SupermarketCreateSubscription | None = None
    promotion: SupermarketCreatePromotion | None = None


class SupermarketUpdateAddress(BaseModel):
    street_address: str | None = Field(default=None, max_length=250)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=20)
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class SupermarketUpdateRequest(BaseModel):
    shop_name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=100)
    shop_license_no: str | None = Field(default=None, max_length=100)
    photo: str | None = Field(default=None, max_length=255)
    geo_coordinates: dict[str, Any] | None = None
    upi_id: str | None = Field(default=None, max_length=100)
    delivery_time: int | None = Field(default=None, ge=0)
    status: ShopStatus | None = None
    payment_status: ShopPaymentStatus | None = None
    is_blocked: bool | None = None
    address: SupermarketUpdateAddress | None = None


class SupermarketDetailAddress(BaseModel):
    street_address: str
    city: str
    state: str
    pincode: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class SupermarketDetailSubscription(BaseModel):
    subscription_id: int
    start_date: datetime
    end_date: datetime
    amount: Decimal
    status: str
    last_payment_date: datetime | None = None


class SupermarketDetailPromotion(BaseModel):
    promotion_link: str | None = None
    promotion_header: str | None = None
    promotion_content: str | None = None
    promotion_image_s3_key: str | None = None
    is_marketing_enabled: bool


class SupermarketDetailDeliveryPartner(BaseModel):
    delivery_partner_id: str
    first_name: str
    last_name: str | None = None
    phone1: int
    email: str | None = None
    online_status: str
    current_status: str
    photo: str
    vehicle_detail: str | None = None
    rating: Decimal | None = None
    created_at: datetime


class SupermarketDetailInvoice(BaseModel):
    invoice_id: int
    invoice_number: str
    billing_period_start: datetime
    billing_period_end: datetime
    amount: Decimal
    status: str
    document_type: str
    paid_at: datetime | None = None
    created_at: datetime


class SupermarketDailyOrderStat(BaseModel):
    date: str
    order_count: int
    total_amount: Decimal
    status_counts: dict[str, int]


class SupermarketDetailShopOwner(BaseModel):
    shop_id: str
    user_id: int
    shop_name: str
    phone: str | None = None
    email: str | None = None
    photo: str | None = None
    status: str
    payment_status: str
    is_blocked: bool
    geo_coordinates: dict[str, Any] | None = None
    upi_id: str | None = None
    rating: Decimal | None = None
    delivery_time: int | None = None
    created_at: datetime
    updated_at: datetime


class SupermarketDetailResponse(BaseModel):
    shop_owner: SupermarketDetailShopOwner
    address: SupermarketDetailAddress
    subscription: SupermarketDetailSubscription | None = None
    promotion: SupermarketDetailPromotion | None = None
    delivery_partners: list[SupermarketDetailDeliveryPartner]
    subscription_invoices: list[SupermarketDetailInvoice]
    daily_order_stats: list[SupermarketDailyOrderStat] | None = None

