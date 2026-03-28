from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.api.v1.schemas.subscription_invoice import SubscriptionInvoiceCreate, SubscriptionInvoiceUpdate
from app.infrastructure.db.models.enums import InvoiceDocumentType
from app.infrastructure.db.models.subscription import Subscription
from app.infrastructure.db.models.subscription_invoice import SubscriptionInvoice


class AbstractInvoiceRepository(ABC):
    @abstractmethod
    def list_invoices(
        self,
        *,
        page: int,
        limit: int,
        filters: dict[str, Any],
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[list[SubscriptionInvoice], int]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, invoice_id: int) -> SubscriptionInvoice | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_number(self, invoice_number: str) -> SubscriptionInvoice | None:
        raise NotImplementedError

    @abstractmethod
    def max_invoice_sequence_suffix(
        self,
        *,
        document_type: InvoiceDocumentType,
        prefix: str,
        ym: str,
    ) -> int:
        """Highest numeric suffix for PREFIX-YYYYMM-#### numbers, or 0 if none."""

    @abstractmethod
    def create_invoice(self, payload: SubscriptionInvoiceCreate) -> SubscriptionInvoice:
        """Create a new invoice or bill. Caller is responsible for ensuring invoice_number uniqueness."""
        raise NotImplementedError

    @abstractmethod
    def update_invoice(
        self,
        invoice: SubscriptionInvoice,
        payload: SubscriptionInvoiceUpdate,
    ) -> SubscriptionInvoice:
        raise NotImplementedError

    @abstractmethod
    def exists_for_shop_period_type(
        self,
        *,
        shop_id: str,
        billing_period_start: datetime,
        document_type: str,
    ) -> bool:
        """Check uniqueness: one record per shop + period + type."""
        raise NotImplementedError

    @abstractmethod
    def monthly_summary(self, *, year: int, month: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_subscriptions(self) -> list[Subscription]:
        raise NotImplementedError

    @abstractmethod
    def list_pending_invoices(self) -> list[SubscriptionInvoice]:
        raise NotImplementedError

    @abstractmethod
    def list_issued_invoices_for_current_month(self) -> list[SubscriptionInvoice]:
        """ISSUED invoices for current billing month (document_type=INVOICE)."""
        raise NotImplementedError

    @abstractmethod
    def get_accounts_overview(
        self,
        *,
        days: int,
        shop_id: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

