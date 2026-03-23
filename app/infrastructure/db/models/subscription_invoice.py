from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.enums import InvoiceDocumentType, InvoiceStatus
from app.infrastructure.db.models.mixins import TimestampMixin


class SubscriptionInvoice(Base, TimestampMixin):
    __tablename__ = "subscription_invoices"
    __table_args__ = (
        UniqueConstraint(
            "shop_id",
            "billing_period_start",
            "document_type",
            name="uq_subscription_invoices_shop_period_type",
        ),
        Index("ix_subscription_invoices_shop_id", "shop_id"),
        Index("ix_subscription_invoices_subscription_id", "subscription_id"),
        Index("ix_subscription_invoices_status", "status"),
    )

    invoice_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.subscription_id"), nullable=False
    )
    shop_id: Mapped[str] = mapped_column(ForeignKey("shop_owners.shop_id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    billing_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    billing_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    other_charges: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    cgst: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    igst: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    sgst: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_type: Mapped[InvoiceDocumentType] = mapped_column(
        Enum(InvoiceDocumentType, name="invoice_document_type"),
        default=InvoiceDocumentType.INVOICE,
        nullable=False,
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status"),
        default=InvoiceStatus.PENDING,
        nullable=False,
    )
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transaction_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bank_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    subscription = relationship("Subscription", back_populates="subscription_invoices")
    shop_owner = relationship("ShopOwner", back_populates="subscription_invoices")

