from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.infrastructure.db.models.enums import InvoiceDocumentType, InvoiceStatus


class SubscriptionInvoiceBase(BaseModel):
    subscription_id: int
    shop_id: str
    invoice_number: str
    billing_period_start: datetime
    billing_period_end: datetime
    amount: Decimal
    discount: Decimal = Decimal("0")
    other_charges: Decimal = Decimal("0")
    cgst: Decimal = Decimal("0")
    igst: Decimal = Decimal("0")
    sgst: Decimal = Decimal("0")
    document_type: InvoiceDocumentType = InvoiceDocumentType.INVOICE
    status: InvoiceStatus = InvoiceStatus.PENDING


class SubscriptionInvoiceCreate(SubscriptionInvoiceBase):
    pass


class SubscriptionInvoiceUpdate(BaseModel):
    amount: Decimal | None = None
    discount: Decimal | None = None
    other_charges: Decimal | None = None
    cgst: Decimal | None = None
    igst: Decimal | None = None
    sgst: Decimal | None = None
    description: str | None = None
    notes: str | None = None
    document_type: InvoiceDocumentType | None = None
    status: InvoiceStatus | None = None
    pdf_url: str | None = None
    transaction_reference: str | None = None
    paid_at: datetime | None = None
    bank_details: dict[str, Any] | None = None


class SubscriptionInvoiceRead(SubscriptionInvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: int
    description: str | None = None
    notes: str | None = None
    pdf_url: str | None = None
    transaction_reference: str | None = None
    paid_at: datetime | None = None
    bank_details: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class SubscriptionInvoiceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: int
    invoice_number: str
    shop_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    amount: Decimal
    status: InvoiceStatus

