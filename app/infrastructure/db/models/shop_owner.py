from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
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
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.enums import ShopPaymentStatus, ShopStatus
from app.infrastructure.db.models.mixins import SoftDeleteMixin, TimestampMixin


class ShopOwner(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "shop_owners"
    __table_args__ = (
        Index("ix_shop_owners_phone", "phone"),
        Index("ix_shop_owners_status_is_deleted", "status", "is_deleted"),
        Index("ix_shop_owners_address_id", "address_id"),
        Index(
            "uq_shop_owners_email_not_null",
            "email",
            unique=True,
            postgresql_where=text("email IS NOT NULL"),
        ),
        Index(
            "uq_shop_owners_hmac_secret_not_null",
            "hmac_secret",
            unique=True,
            postgresql_where=text("hmac_secret IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    shop_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shop_license_no: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    photo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"), nullable=False)
    subscription_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    status: Mapped[ShopStatus] = mapped_column(
        Enum(ShopStatus, name="shop_status"), default=ShopStatus.ACTIVE, nullable=False
    )
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payment_status: Mapped[ShopPaymentStatus] = mapped_column(
        Enum(ShopPaymentStatus, name="shop_payment_status"),
        default=ShopPaymentStatus.PENDING,
        nullable=False,
    )
    contact_person_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_person_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_sms_activated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    single_sms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_web_app: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    geo_coordinates: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    auto_assigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_assigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_supermarket: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hmac_secret: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_time: Mapped[int | None] = mapped_column(Integer, default=30, nullable=True)

    address = relationship("Address", back_populates="shop_owners")
    delivery_partners = relationship("DeliveryPartner", back_populates="shop_owner")
    orders = relationship("Order", back_populates="shop_owner")
    subscriptions = relationship("Subscription", back_populates="shop_owner")
    subscription_invoices = relationship("SubscriptionInvoice", back_populates="shop_owner")
    promotion = relationship("ShopOwnerPromotion", back_populates="shop_owner", uselist=False)
    customer_order_addresses = relationship(
        "CustomerOrderAddress", back_populates="shop_owner"
    )

