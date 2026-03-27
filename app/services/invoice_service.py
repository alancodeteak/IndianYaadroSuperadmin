from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.subscription_invoice import (
    SubscriptionInvoiceCreate,
    SubscriptionInvoiceListItem,
    SubscriptionInvoiceRead,
    SubscriptionInvoiceUpdate,
)
from app.domain.repositories.invoice_repository import AbstractInvoiceRepository
from app.infrastructure.db.models.enums import InvoiceDocumentType, InvoiceStatus
from app.infrastructure.db.models.subscription_invoice import SubscriptionInvoice


@dataclass(frozen=True)
class InvoiceNumberGenerator:
    prefix_invoice: str = "INV"
    prefix_bill: str = "BILL"

    def generate(self, *, document_type: InvoiceDocumentType, now: datetime, next_sequence: int) -> str:
        ym = now.strftime("%Y%m")
        seq = f"{next_sequence:04d}"
        if document_type == InvoiceDocumentType.BILL:
            return f"{self.prefix_bill}-{ym}-{seq}"
        return f"{self.prefix_invoice}-{ym}-{seq}"


class InvoiceService:
    def __init__(self, repository: AbstractInvoiceRepository):
        self.repository = repository
        self.number_generator = InvoiceNumberGenerator()

    def list_invoices(
        self,
        *,
        page: int,
        limit: int,
        filters: dict[str, Any],
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[list[SubscriptionInvoiceListItem], int]:
        if page < 1:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="page must be >= 1",
                status_code=400,
            )
        if limit < 1 or limit > 200:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="limit must be between 1 and 200",
                status_code=400,
            )

        rows, total = self.repository.list_invoices(page=page, limit=limit, filters=filters, order_by=order_by)
        items = [SubscriptionInvoiceListItem.model_validate(r) for r in rows]
        return items, total

    def get_invoice(self, invoice_id: int) -> SubscriptionInvoiceRead:
        if invoice_id <= 0:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="invoice_id must be > 0",
                status_code=400,
            )
        invoice = self.repository.get_by_id(invoice_id)
        if not invoice:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Invoice not found",
                status_code=404,
            )
        return SubscriptionInvoiceRead.model_validate(invoice)

    def _validate_amounts(self, payload: SubscriptionInvoiceCreate | SubscriptionInvoiceUpdate) -> None:
        data = payload.model_dump(exclude_unset=True)
        for key in ("amount", "discount", "other_charges", "cgst", "igst", "sgst"):
            if key in data and data[key] is not None:
                value = Decimal(str(data[key]))
                if value < 0:
                    raise ApiError(
                        code=ErrorCode.VALIDATION_ERROR,
                        message=f"{key} cannot be negative",
                        status_code=400,
                    )

    def create_manual_invoice(self, payload: SubscriptionInvoiceCreate) -> SubscriptionInvoiceRead:
        self._validate_amounts(payload)
        # Enforce uniqueness: one per shop + billing period start + type
        if self.repository.exists_for_shop_period_type(
            shop_id=payload.shop_id,
            billing_period_start=payload.billing_period_start,
            document_type=payload.document_type.value,
        ):
            raise ApiError(
                code=ErrorCode.CONFLICT,
                message="An invoice already exists for this shop, billing period, and document type",
                status_code=409,
            )
        # Invoice number is provided externally; keep old behavior for backfill/manuals
        created = self.repository.create_invoice(payload)
        return SubscriptionInvoiceRead.model_validate(created)

    def _next_sequence(self, *, document_type: InvoiceDocumentType, now: datetime) -> int:
        prefix = "INV" if document_type == InvoiceDocumentType.INVOICE else "BILL"
        ym = now.strftime("%Y%m")
        rows, _ = self.repository.list_invoices(
            page=1,
            limit=9999,
            filters={"document_type": document_type, "search": f"{prefix}-{ym}-"},
            order_by=[("invoice_number", "desc")],
        )
        best = 0
        for row in rows:
            parts = row.invoice_number.split("-")
            if len(parts) != 3:
                continue
            if parts[0] != prefix or parts[1] != ym:
                continue
            try:
                best = max(best, int(parts[2]))
            except ValueError:
                continue
        return best + 1

    def create_system_invoice(
        self,
        *,
        subscription_id: int,
        shop_id: str,
        billing_period_start: datetime,
        billing_period_end: datetime,
        amount: Decimal,
        discount: Decimal = Decimal("0"),
        other_charges: Decimal = Decimal("0"),
        cgst: Decimal = Decimal("0"),
        igst: Decimal = Decimal("0"),
        sgst: Decimal = Decimal("0"),
        description: str | None = None,
        notes: str | None = None,
        document_type: InvoiceDocumentType = InvoiceDocumentType.INVOICE,
        status: InvoiceStatus = InvoiceStatus.ISSUED,
    ) -> SubscriptionInvoiceRead:
        if self.repository.exists_for_shop_period_type(
            shop_id=shop_id,
            billing_period_start=billing_period_start,
            document_type=document_type.value,
        ):
            raise ApiError(
                code=ErrorCode.CONFLICT,
                message="Document already exists for this shop and period",
                status_code=409,
            )
        now = datetime.now(timezone.utc)
        next_seq = self._next_sequence(document_type=document_type, now=now)
        invoice_number = self.number_generator.generate(document_type=document_type, now=now, next_sequence=next_seq)
        payload = SubscriptionInvoiceCreate(
            subscription_id=subscription_id,
            shop_id=shop_id,
            invoice_number=invoice_number,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            amount=amount,
            discount=discount,
            other_charges=other_charges,
            cgst=cgst,
            igst=igst,
            sgst=sgst,
            document_type=document_type,
            status=status,
        )
        if description:
            object.__setattr__(payload, "description", description)
        if notes:
            object.__setattr__(payload, "notes", notes)
        self._validate_amounts(payload)
        created = self.repository.create_invoice(payload)
        return SubscriptionInvoiceRead.model_validate(created)

    def update_invoice(self, invoice_id: int, payload: SubscriptionInvoiceUpdate) -> SubscriptionInvoiceRead:
        invoice = self._require_invoice(invoice_id)
        data = payload.model_dump(exclude_unset=True)
        # Protect invoice_number from updates
        if "invoice_number" in data:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="invoice_number cannot be modified",
                status_code=400,
            )
        # Limit edits when PAID
        if invoice.status == InvoiceStatus.PAID:
            forbidden_keys = {"amount", "discount", "other_charges", "cgst", "igst", "sgst", "billing_period_start", "billing_period_end"}
            if any(k in data for k in forbidden_keys):
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Paid invoices have restricted editable fields",
                    status_code=400,
                )
        self._validate_amounts(payload)
        updated = self.repository.update_invoice(invoice, payload)
        return SubscriptionInvoiceRead.model_validate(updated)

    def _require_invoice(self, invoice_id: int) -> SubscriptionInvoice:
        if invoice_id <= 0:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="invoice_id must be > 0",
                status_code=400,
            )
        invoice = self.repository.get_by_id(invoice_id)
        if not invoice:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Invoice not found",
                status_code=404,
            )
        return invoice

    def update_status(
        self,
        invoice_id: int,
        *,
        new_status: InvoiceStatus,
        paid_at: datetime | None = None,
        transaction_reference: str | None = None,
    ) -> SubscriptionInvoiceRead:
        invoice = self._require_invoice(invoice_id)
        self._ensure_valid_transition(invoice.status, new_status)

        update_data: dict[str, Any] = {"status": new_status}

        if new_status == InvoiceStatus.PAID:
            now = datetime.now(timezone.utc)
            if paid_at is None:
                paid_at = now
            if paid_at > now:
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="paid_at cannot be in the future",
                    status_code=400,
                )
            if not transaction_reference:
                raise ApiError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="transaction_reference is required when marking invoice as PAID",
                    status_code=400,
                )
            update_data["paid_at"] = paid_at
            update_data["transaction_reference"] = transaction_reference

        update_payload = SubscriptionInvoiceUpdate(**update_data)
        updated = self.repository.update_invoice(invoice, update_payload)
        if new_status == InvoiceStatus.PAID and updated.document_type == InvoiceDocumentType.INVOICE:
            # Keep invoice status as PAID even if bill generation fails.
            try:
                self.generate_bill_for_invoice(updated.invoice_id)
            except Exception:
                pass
        return SubscriptionInvoiceRead.model_validate(updated)

    def generate_bill_for_invoice(self, invoice_id: int) -> SubscriptionInvoiceRead:
        invoice = self._require_invoice(invoice_id)
        if invoice.document_type != InvoiceDocumentType.INVOICE:
            raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="Bills cannot generate bills", status_code=400)
        if invoice.status != InvoiceStatus.PAID:
            raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="Only PAID invoices can generate bills", status_code=400)

        if self.repository.exists_for_shop_period_type(
            shop_id=invoice.shop_id,
            billing_period_start=invoice.billing_period_start,
            document_type=InvoiceDocumentType.BILL.value,
        ):
            rows, _ = self.repository.list_invoices(
                page=1,
                limit=1,
                filters={
                    "shop_id": invoice.shop_id,
                    "document_type": InvoiceDocumentType.BILL,
                    "billing_period_start": invoice.billing_period_start,
                    "billing_period_end": invoice.billing_period_end,
                },
                order_by=[("invoice_id", "desc")],
            )
            if rows:
                return SubscriptionInvoiceRead.model_validate(rows[0])
            raise ApiError(code=ErrorCode.CONFLICT, message="Bill already exists", status_code=409)

        return self.create_system_invoice(
            subscription_id=invoice.subscription_id,
            shop_id=invoice.shop_id,
            billing_period_start=invoice.billing_period_start,
            billing_period_end=invoice.billing_period_end,
            amount=invoice.amount,
            discount=invoice.discount,
            other_charges=invoice.other_charges,
            cgst=invoice.cgst,
            igst=invoice.igst,
            sgst=invoice.sgst,
            description=invoice.description,
            notes=invoice.notes,
            document_type=InvoiceDocumentType.BILL,
            status=InvoiceStatus.ISSUED,
        )

    def generate_monthly(self, *, year: int, month: int) -> dict[str, int]:
        generated = 0
        skipped = 0
        for subscription in self.repository.list_subscriptions():
            start = datetime(year=year, month=month, day=1, tzinfo=timezone.utc)
            if subscription.start_date > start:
                skipped += 1
                continue
            end_month = (start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            try:
                self.create_system_invoice(
                    subscription_id=subscription.subscription_id,
                    shop_id=subscription.shop_id,
                    billing_period_start=start,
                    billing_period_end=end_month,
                    amount=Decimal(str(subscription.amount)),
                    document_type=InvoiceDocumentType.INVOICE,
                    status=InvoiceStatus.ISSUED,
                )
                generated += 1
            except ApiError as e:
                if e.code == ErrorCode.CONFLICT:
                    skipped += 1
                    continue
                raise
        return {"generated": generated, "skipped": skipped}

    def run_overdue_automation(self) -> dict[str, int]:
        transitioned = 0
        now = datetime.now(timezone.utc)
        for invoice in self.repository.list_pending_invoices():
            next_invoice_date = (invoice.billing_period_start + timedelta(days=32)).replace(day=1)
            overdue_trigger = next_invoice_date - timedelta(days=5)
            if now >= overdue_trigger:
                self.repository.update_invoice(
                    invoice,
                    SubscriptionInvoiceUpdate(status=InvoiceStatus.OVERDUE),
                )
                transitioned += 1
        return {"transitioned_to_overdue": transitioned}

    def retry_bill_generation(self, invoice_id: int) -> SubscriptionInvoiceRead:
        return self.generate_bill_for_invoice(invoice_id)

    def sync_notes_between_invoice_and_bill(self, invoice_id: int) -> dict[str, int]:
        invoice = self._require_invoice(invoice_id)
        target_type = InvoiceDocumentType.BILL if invoice.document_type == InvoiceDocumentType.INVOICE else InvoiceDocumentType.INVOICE
        rows, _ = self.repository.list_invoices(
            page=1,
            limit=1,
            filters={
                "shop_id": invoice.shop_id,
                "document_type": target_type,
                "billing_period_start": invoice.billing_period_start,
                "billing_period_end": invoice.billing_period_end,
            },
            order_by=[("updated_at", "desc")],
        )
        if not rows:
            return {"synced": 0}
        peer = rows[0]
        latest = invoice if invoice.updated_at >= peer.updated_at else peer
        note_value = latest.notes
        self.repository.update_invoice(invoice, SubscriptionInvoiceUpdate(notes=note_value))
        self.repository.update_invoice(peer, SubscriptionInvoiceUpdate(notes=note_value))
        return {"synced": 1}

    def import_legacy_documents(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        imported = 0
        skipped = 0
        for row in rows:
            invoice_number = str(row.get("invoice_number") or "").strip()
            if not invoice_number:
                skipped += 1
                continue
            if self.repository.get_by_number(invoice_number):
                skipped += 1
                continue
            payload = SubscriptionInvoiceCreate(
                subscription_id=int(row["subscription_id"]),
                shop_id=str(row["shop_id"]),
                invoice_number=invoice_number,
                billing_period_start=row["billing_period_start"],
                billing_period_end=row["billing_period_end"],
                amount=Decimal(str(row.get("amount", "0"))),
                discount=Decimal(str(row.get("discount", "0"))),
                other_charges=Decimal(str(row.get("other_charges", "0"))),
                cgst=Decimal(str(row.get("cgst", "0"))),
                igst=Decimal(str(row.get("igst", "0"))),
                sgst=Decimal(str(row.get("sgst", "0"))),
                document_type=InvoiceDocumentType(str(row.get("document_type", "INVOICE"))),
                status=InvoiceStatus(str(row.get("status", "ISSUED"))),
            )
            self.repository.create_invoice(payload)
            imported += 1
        return {"imported": imported, "skipped": skipped}

    def _ensure_valid_transition(self, current: InvoiceStatus, new: InvoiceStatus) -> None:
        if current == new:
            return

        allowed: dict[InvoiceStatus, set[InvoiceStatus]] = {
            InvoiceStatus.ISSUED: {InvoiceStatus.PENDING, InvoiceStatus.PAID, InvoiceStatus.VOID, InvoiceStatus.FAILED},
            InvoiceStatus.PENDING: {InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.VOID, InvoiceStatus.FAILED},
            InvoiceStatus.OVERDUE: {InvoiceStatus.PAID, InvoiceStatus.VOID},
            InvoiceStatus.FAILED: {InvoiceStatus.ISSUED, InvoiceStatus.PENDING, InvoiceStatus.VOID},
            InvoiceStatus.PAID: {InvoiceStatus.VOID},
            InvoiceStatus.VOID: set(),
        }
        if new not in allowed.get(current, set()):
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"Cannot transition invoice from {current.value} to {new.value}",
                status_code=400,
            )

