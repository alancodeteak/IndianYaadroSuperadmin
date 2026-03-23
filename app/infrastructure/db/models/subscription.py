from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.enums import SubscriptionStatus
from app.infrastructure.db.models.mixins import TimestampMixin


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_shop_id", "shop_id"),
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_end_date", "end_date"),
    )

    subscription_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shop_owners.shop_id"), nullable=False, unique=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
    )
    last_payment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shop_owner = relationship("ShopOwner", back_populates="subscriptions")
    subscription_invoices = relationship("SubscriptionInvoice", back_populates="subscription")

