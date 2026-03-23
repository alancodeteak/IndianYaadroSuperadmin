from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.mixins import SoftDeleteMixin, TimestampMixin


class CustomerOrderAddress(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customer_order_addresses"
    __table_args__ = (
        Index("ix_customer_order_addresses_phone", "customer_phone_number"),
        Index("ix_customer_order_addresses_name", "customer_name"),
        Index("ix_customer_order_addresses_shop_id", "shop_id"),
        Index("ix_customer_order_addresses_pay_later", "pay_later"),
        Index("ix_customer_order_addresses_created_at", "created_at"),
        Index(
            "uq_customer_order_addresses_phone_shop",
            "customer_phone_number",
            "shop_id",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shop_owners.shop_id"), nullable=False)
    credit_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    debit_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    current_month_order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    previous_month_order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_month_total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=0, nullable=False
    )
    previous_month_total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=0, nullable=False
    )
    current_month_tracked: Mapped[str | None] = mapped_column(String(7), nullable=True)
    previous_month_tracked: Mapped[str | None] = mapped_column(String(7), nullable=True)
    pay_later: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    shop_owner = relationship("ShopOwner", back_populates="customer_order_addresses")

