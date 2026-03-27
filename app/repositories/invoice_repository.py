from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.v1.schemas.subscription_invoice import SubscriptionInvoiceCreate, SubscriptionInvoiceUpdate
from app.domain.repositories.invoice_repository import AbstractInvoiceRepository
from app.infrastructure.db.models.enums import InvoiceDocumentType
from app.infrastructure.db.models.enums import InvoiceStatus, SubscriptionStatus
from app.infrastructure.db.models.subscription import Subscription
from app.infrastructure.db.models.subscription_invoice import SubscriptionInvoice


class InvoiceRepository(AbstractInvoiceRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_invoices(
        self,
        *,
        page: int,
        limit: int,
        filters: dict[str, Any],
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[list[SubscriptionInvoice], int]:
        conditions: list[Any] = []

        if shop_id := filters.get("shop_id"):
            conditions.append(SubscriptionInvoice.shop_id == shop_id)
        if status := filters.get("status"):
            conditions.append(SubscriptionInvoice.status == status)
        if document_type := filters.get("document_type"):
            conditions.append(SubscriptionInvoice.document_type == document_type)
        if subscription_id := filters.get("subscription_id"):
            conditions.append(SubscriptionInvoice.subscription_id == subscription_id)
        if billing_start := filters.get("billing_period_start"):
            conditions.append(SubscriptionInvoice.billing_period_start >= billing_start)
        if billing_end := filters.get("billing_period_end"):
            conditions.append(SubscriptionInvoice.billing_period_end <= billing_end)
        if created_from := filters.get("created_from"):
            conditions.append(SubscriptionInvoice.created_at >= created_from)
        if created_to := filters.get("created_to"):
            conditions.append(SubscriptionInvoice.created_at <= created_to)
        if search := (filters.get("search") or "").strip():
            like = f"%{search}%"
            conditions.append(SubscriptionInvoice.invoice_number.ilike(like))

        count_stmt = select(func.count(SubscriptionInvoice.invoice_id)).where(and_(*conditions))
        total = int(self.db.scalar(count_stmt) or 0)

        stmt = select(SubscriptionInvoice).where(and_(*conditions))

        for field, direction in order_by or []:
            column = getattr(SubscriptionInvoice, field, None)
            if column is None:
                continue
            if direction.lower() == "desc":
                stmt = stmt.order_by(column.desc())
            else:
                stmt = stmt.order_by(column.asc())

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        rows = list(self.db.scalars(stmt).all())
        return rows, total

    def get_by_id(self, invoice_id: int) -> SubscriptionInvoice | None:
        return self.db.get(SubscriptionInvoice, invoice_id)

    def get_by_number(self, invoice_number: str) -> SubscriptionInvoice | None:
        stmt = select(SubscriptionInvoice).where(SubscriptionInvoice.invoice_number == invoice_number)
        return self.db.scalar(stmt)

    def create_invoice(self, payload: SubscriptionInvoiceCreate) -> SubscriptionInvoice:
        invoice = SubscriptionInvoice(**payload.model_dump())
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def update_invoice(
        self,
        invoice: SubscriptionInvoice,
        payload: SubscriptionInvoiceUpdate,
    ) -> SubscriptionInvoice:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(invoice, key, value)
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def exists_for_shop_period_type(
        self,
        *,
        shop_id: str,
        billing_period_start: datetime,
        document_type: str,
    ) -> bool:
        stmt = select(func.count(SubscriptionInvoice.invoice_id)).where(
            SubscriptionInvoice.shop_id == shop_id,
            SubscriptionInvoice.billing_period_start == billing_period_start,
            SubscriptionInvoice.document_type
            == (InvoiceDocumentType(document_type) if not isinstance(document_type, InvoiceDocumentType) else document_type),
        )
        return bool(self.db.scalar(stmt) or 0)

    def monthly_summary(self, *, year: int, month: int) -> list[dict[str, Any]]:
        stmt = (
            select(
                SubscriptionInvoice.document_type,
                func.count(SubscriptionInvoice.invoice_id).label("count"),
                func.coalesce(func.sum(SubscriptionInvoice.amount), 0).label("amount"),
            )
            .where(
                func.extract("year", SubscriptionInvoice.billing_period_start) == year,
                func.extract("month", SubscriptionInvoice.billing_period_start) == month,
            )
            .group_by(SubscriptionInvoice.document_type)
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                "document_type": str(row.document_type),
                "count": int(row.count or 0),
                "amount": float(row.amount or 0),
            }
            for row in rows
        ]

    def list_subscriptions(self) -> list[Subscription]:
        stmt = select(Subscription).where(Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]))
        return list(self.db.scalars(stmt).all())

    def list_pending_invoices(self) -> list[SubscriptionInvoice]:
        stmt = select(SubscriptionInvoice).where(
            SubscriptionInvoice.document_type == InvoiceDocumentType.INVOICE,
            SubscriptionInvoice.status == InvoiceStatus.PENDING,
        )
        return list(self.db.scalars(stmt).all())

