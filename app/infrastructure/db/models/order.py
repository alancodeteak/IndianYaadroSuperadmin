from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.enums import (
    OrderPaymentMode,
    OrderPaymentStatus,
    OrderStatus,
    OrderUrgency,
)
from app.infrastructure.db.models.mixins import SoftDeleteMixin, TimestampMixin


class Order(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_is_deleted", "is_deleted"),
        Index("ix_orders_created_at", "created_at"),
        Index("ix_orders_shop_deleted", "shop_id", "is_deleted"),
        Index("ix_orders_status_deleted", "order_status", "is_deleted"),
        Index("ix_orders_partner_deleted", "delivery_partner_id", "is_deleted"),
        Index("ix_orders_bill_deleted", "bill_no", "is_deleted"),
        Index("ix_orders_tracking_deleted", "tracking_token", "is_deleted"),
        Index("ix_orders_feedback_token", "feedback_token"),
        Index("ix_orders_shop_status_deleted", "shop_id", "order_status", "is_deleted"),
        Index(
            "ix_orders_partner_status_deleted",
            "delivery_partner_id",
            "order_status",
            "is_deleted",
        ),
        Index("ix_orders_shop_created_deleted", "shop_id", "created_at", "is_deleted"),
        Index("ix_orders_shop_delivered_deleted", "shop_id", "delivered_at", "is_deleted"),
        Index(
            "uq_orders_shop_bill_not_deleted",
            "shop_id",
            "bill_no",
            unique=True,
            postgresql_where=text("is_deleted = false AND bill_no IS NOT NULL"),
        ),
    )

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shop_owners.shop_id"), nullable=False)
    delivery_partner_id: Mapped[str | None] = mapped_column(
        ForeignKey("delivery_partners.delivery_partner_id"), nullable=True
    )
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    bill_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_phone_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    order_status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), nullable=False
    )
    payment_mode: Mapped[OrderPaymentMode | None] = mapped_column(
        Enum(OrderPaymentMode, name="order_payment_mode"), nullable=True
    )
    payment_status: Mapped[OrderPaymentStatus] = mapped_column(
        Enum(OrderPaymentStatus, name="order_payment_status"),
        default=OrderPaymentStatus.PENDING,
        nullable=False,
    )
    special_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_time_arrival: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    time_period: Mapped[str | None] = mapped_column(String(50), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_proof: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    bill_image: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    payment_verification: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    upi_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    online_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cash_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    credit_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    prepaid_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    advanced_payment: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    utr: Mapped[str | None] = mapped_column(String(100), nullable=True)
    water: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    water_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    counter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    urgency: Mapped[OrderUrgency] = mapped_column(
        Enum(OrderUrgency, name="order_urgency"), default=OrderUrgency.NORMAL, nullable=False
    )
    is_address_updated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tracking_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tracking_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tracking_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivery_charge: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    order_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_token: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    pay_later: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blank_order: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blank_order_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)

    shop_owner = relationship("ShopOwner", back_populates="orders")
    delivery_partner = relationship("DeliveryPartner", back_populates="orders")

