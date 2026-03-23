from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.infrastructure.db.models.enums import (
    OrderPaymentMode,
    OrderPaymentStatus,
    OrderStatus,
    OrderUrgency,
)


class OrderBase(BaseModel):
    shop_id: str
    delivery_partner_id: str | None = None
    address: str
    bill_no: str | None = None
    customer_name: str
    customer_phone_number: int
    total_amount: Decimal
    order_status: OrderStatus
    payment_mode: OrderPaymentMode | None = None
    payment_status: OrderPaymentStatus = OrderPaymentStatus.PENDING
    delivery_charge: Decimal = Decimal("0")
    is_deleted: bool = False


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    delivery_partner_id: str | None = None
    address: str | None = None
    bill_no: str | None = None
    order_status: OrderStatus | None = None
    payment_mode: OrderPaymentMode | None = None
    payment_status: OrderPaymentStatus | None = None
    special_instructions: str | None = None
    cancellation_reason: str | None = None
    estimated_time_arrival: datetime | None = None
    urgency: OrderUrgency | None = None
    is_address_updated: bool | None = None
    tracking_token: str | None = None
    tracking_token_expires_at: datetime | None = None
    tracking_active: bool | None = None
    delivery_charge: Decimal | None = None
    order_feedback: str | None = None
    pay_later: bool | None = None
    edited: bool | None = None
    notes: dict[str, Any] | list[Any] | None = None


class OrderRead(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    order_at: datetime | None = None
    special_instructions: str | None = None
    cancellation_reason: str | None = None
    assigned_at: datetime | None = None
    picked_up_at: datetime | None = None
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None
    estimated_time_arrival: datetime | None = None
    time_period: str | None = None
    feedback: str | None = None
    payment_proof: str | None = None
    bill_image: str | None = None
    payment_verification: bool
    upi_amount: Decimal | None = None
    online_amount: Decimal | None = None
    cash_amount: Decimal | None = None
    credit_amount: Decimal | None = None
    prepaid_amount: Decimal | None = None
    advanced_payment: Decimal | None = None
    utr: str | None = None
    water: bool
    water_count: int
    counter: str | None = None
    urgency: OrderUrgency
    is_address_updated: bool
    tracking_token: str | None = None
    tracking_token_expires_at: datetime | None = None
    tracking_active: bool
    order_rating: int | None = None
    order_feedback: str | None = None
    feedback_token: str | None = None
    pay_later: bool
    edited: bool
    is_blank_order: bool
    blank_order_at: datetime | None = None
    notes: dict[str, Any] | list[Any] | None = None
    created_at: datetime
    updated_at: datetime


class OrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    shop_id: str
    bill_no: str | None = None
    customer_name: str
    total_amount: Decimal
    order_status: OrderStatus
    payment_status: OrderPaymentStatus
    created_at: datetime

