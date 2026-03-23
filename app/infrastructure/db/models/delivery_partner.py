from datetime import datetime, timezone
from decimal import Decimal

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
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.enums import DeliveryOnlineStatus, DeliveryPartnerStatus
from app.infrastructure.db.models.mixins import SoftDeleteMixin, TimestampMixin


class DeliveryPartner(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "delivery_partners"
    __table_args__ = (
        Index("ix_delivery_partners_shop_status", "shop_id", "current_status"),
        Index("ix_delivery_partners_phone1", "phone1"),
        Index("ix_delivery_partners_online_current", "online_status", "current_status"),
        Index("ix_delivery_partners_shop_deleted", "shop_id", "is_deleted"),
        Index(
            "uq_delivery_partners_hmac_secret_not_null",
            "hmac_secret",
            unique=True,
            postgresql_where=text("hmac_secret IS NOT NULL"),
        ),
    )

    delivery_partner_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shop_owners.shop_id"), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    license_no: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    license_image: Mapped[str] = mapped_column(Text, nullable=False)
    govt_id_image: Mapped[str | None] = mapped_column(Text, nullable=True)
    join_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_status: Mapped[DeliveryPartnerStatus] = mapped_column(
        Enum(DeliveryPartnerStatus, name="delivery_partner_status"),
        default=DeliveryPartnerStatus.IDLE,
        nullable=False,
    )
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    phone1: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    phone2: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    online_status: Mapped[DeliveryOnlineStatus] = mapped_column(
        Enum(DeliveryOnlineStatus, name="delivery_online_status"),
        default=DeliveryOnlineStatus.OFFLINE,
        nullable=False,
    )
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    photo: Mapped[str] = mapped_column(String(1000), nullable=False)
    device_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_order: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vehicle_detail: Mapped[str | None] = mapped_column(String(200), nullable=True)
    total_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    liquid_cash: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    hmac_secret: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    shop_owner = relationship("ShopOwner", back_populates="delivery_partners")
    orders = relationship("Order", back_populates="delivery_partner")

