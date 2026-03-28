from __future__ import annotations

from datetime import datetime
from typing import Any

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, case, distinct, func, select
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

    def max_invoice_sequence_suffix(
        self,
        *,
        document_type: InvoiceDocumentType,
        prefix: str,
        ym: str,
    ) -> int:
        pattern = f"%{prefix}-{ym}-%"
        stmt = select(func.max(SubscriptionInvoice.invoice_number)).where(
            SubscriptionInvoice.document_type == document_type,
            SubscriptionInvoice.invoice_number.ilike(pattern),
        )
        max_number = self.db.scalar(stmt)
        if not max_number:
            return 0
        parts = str(max_number).split("-")
        if len(parts) != 3 or parts[0] != prefix or parts[1] != ym:
            return 0
        try:
            return int(parts[2])
        except ValueError:
            return 0

    def create_invoice(self, payload: SubscriptionInvoiceCreate) -> SubscriptionInvoice:
        invoice = SubscriptionInvoice(**payload.model_dump())
        self.db.add(invoice)
        self.db.flush()
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
        self.db.flush()
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

    def list_issued_invoices_for_current_month(self) -> list[SubscriptionInvoice]:
        now = datetime.now(timezone.utc)
        month_start = datetime(year=now.year, month=now.month, day=1, tzinfo=timezone.utc)
        next_month_start = (month_start + timedelta(days=32)).replace(day=1)
        stmt = select(SubscriptionInvoice).where(
            SubscriptionInvoice.document_type == InvoiceDocumentType.INVOICE,
            SubscriptionInvoice.status == InvoiceStatus.ISSUED,
            SubscriptionInvoice.billing_period_start >= month_start,
            SubscriptionInvoice.billing_period_start < next_month_start,
        )
        return list(self.db.scalars(stmt).all())

    def get_accounts_overview(self, *, days: int, shop_id: str | None = None) -> dict[str, Any]:
        days = max(1, min(int(days), 365))
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=days)

        base_conditions: list[Any] = [SubscriptionInvoice.document_type == InvoiceDocumentType.INVOICE]
        if shop_id:
            base_conditions.append(SubscriptionInvoice.shop_id == shop_id)

        # Collected = PAID invoices amount (within range)
        collected_stmt = select(func.coalesce(func.sum(SubscriptionInvoice.amount), 0)).where(
            and_(*base_conditions),
            SubscriptionInvoice.status == InvoiceStatus.PAID,
            SubscriptionInvoice.paid_at.is_not(None),
            SubscriptionInvoice.paid_at >= since,
        )
        collected_amount = float(self.db.scalar(collected_stmt) or 0)

        # To-collect = pending + overdue invoice amounts (regardless of range)
        to_collect_stmt = select(func.coalesce(func.sum(SubscriptionInvoice.amount), 0)).where(
            and_(*base_conditions),
            SubscriptionInvoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
        )
        to_collect_amount = float(self.db.scalar(to_collect_stmt) or 0)

        overdue_shops_stmt = select(func.count(distinct(SubscriptionInvoice.shop_id))).where(
            and_(*base_conditions),
            SubscriptionInvoice.status == InvoiceStatus.OVERDUE,
        )
        pending_shops_stmt = select(func.count(distinct(SubscriptionInvoice.shop_id))).where(
            and_(*base_conditions),
            SubscriptionInvoice.status == InvoiceStatus.PENDING,
        )

        overdue_invoices_stmt = select(func.count(SubscriptionInvoice.invoice_id)).where(
            and_(*base_conditions),
            SubscriptionInvoice.status == InvoiceStatus.OVERDUE,
        )
        pending_invoices_stmt = select(func.count(SubscriptionInvoice.invoice_id)).where(
            and_(*base_conditions),
            SubscriptionInvoice.status == InvoiceStatus.PENDING,
        )

        overdue_shops = int(self.db.scalar(overdue_shops_stmt) or 0)
        pending_shops = int(self.db.scalar(pending_shops_stmt) or 0)
        overdue_invoices = int(self.db.scalar(overdue_invoices_stmt) or 0)
        pending_invoices = int(self.db.scalar(pending_invoices_stmt) or 0)

        daily_collected_stmt = (
            select(
                func.date(SubscriptionInvoice.paid_at).label("date"),
                func.coalesce(func.sum(SubscriptionInvoice.amount), 0).label("amount"),
            )
            .where(
                and_(*base_conditions),
                SubscriptionInvoice.status == InvoiceStatus.PAID,
                SubscriptionInvoice.paid_at.is_not(None),
                SubscriptionInvoice.paid_at >= since,
            )
            .group_by(func.date(SubscriptionInvoice.paid_at))
            .order_by(func.date(SubscriptionInvoice.paid_at))
        )
        daily_rows = self.db.execute(daily_collected_stmt).all()
        daily_collected = [{"date": str(r.date), "amount": float(r.amount or 0)} for r in daily_rows]

        top_overdue_stmt = (
            select(
                SubscriptionInvoice.shop_id.label("shop_id"),
                func.coalesce(func.sum(SubscriptionInvoice.amount), 0).label("amount"),
                func.count(SubscriptionInvoice.invoice_id).label("count"),
            )
            .where(and_(*base_conditions), SubscriptionInvoice.status == InvoiceStatus.OVERDUE)
            .group_by(SubscriptionInvoice.shop_id)
            .order_by(func.coalesce(func.sum(SubscriptionInvoice.amount), 0).desc())
            .limit(10)
        )
        top_rows = self.db.execute(top_overdue_stmt).all()
        top_overdue_shops = [
            {"shop_id": str(r.shop_id), "amount": float(r.amount or 0), "count": int(r.count or 0)} for r in top_rows
        ]

        return {
            "window_days": days,
            "kpis": {
                "collected_amount": collected_amount,
                "to_collect_amount": to_collect_amount,
                "overdue_shops": overdue_shops,
                "pending_shops": pending_shops,
                "overdue_invoices": overdue_invoices,
                "pending_invoices": pending_invoices,
            },
            "series": {
                "daily_collected": daily_collected,
            },
            "lists": {
                "top_overdue_shops": top_overdue_shops,
            },
        }

