from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.api.exceptions.error_codes import ErrorCode
from app.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    DomainValidationError,
    NotFoundError,
    PermissionDeniedError,
)
from app.domain.repositories.shop_owner_repository import AbstractShopOwnerRepository
from app.api.v1.schemas.subscription_invoice import (
    SubscriptionInvoiceCreate,
    SubscriptionInvoiceListItem,
    SubscriptionInvoiceRead,
    SubscriptionInvoiceUpdate,
)
from app.domain.repositories.invoice_repository import AbstractInvoiceRepository
from app.infrastructure.db.models.enums import InvoiceDocumentType, InvoiceStatus
from app.infrastructure.db.transaction import session_commit_scope
from app.infrastructure.db.models.subscription_invoice import SubscriptionInvoice
from app.services.validation import (
    validate_days_range,
    validate_page_and_limit_invoice,
    validate_positive_id,
)

log = logging.getLogger(__name__)


def _empty_accounts_overview(days: int) -> dict[str, Any]:
    return {
        "window_days": days,
        "kpis": {
            "collected_amount": 0.0,
            "to_collect_amount": 0.0,
            "overdue_shops": 0,
            "pending_shops": 0,
            "overdue_invoices": 0,
            "pending_invoices": 0,
        },
        "series": {"daily_collected": []},
        "lists": {"top_overdue_shops": []},
    }


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
    def __init__(
        self,
        repository: AbstractInvoiceRepository,
        session: Session,
        shop_owner_repository: AbstractShopOwnerRepository,
    ):
        self.repository = repository
        self._session = session
        self._shop_owner_repository = shop_owner_repository
        self.number_generator = InvoiceNumberGenerator()

    def resolve_portal_shop_id(self, portal_email: str) -> str | None:
        return self._shop_owner_repository.get_shop_id_by_email(portal_email)

    def ensure_portal_invoice_access(self, portal_email: str, invoice_shop_id: str) -> None:
        shop_id = self.resolve_portal_shop_id(portal_email)
        if not shop_id or shop_id != invoice_shop_id:
            log.info(
                "portal invoice access denied",
                extra={"portal_email": portal_email, "invoice_shop_id": invoice_shop_id},
            )
            raise PermissionDeniedError("Not enough permissions")

    def get_invoice_for_portal(self, portal_email: str, invoice_id: int) -> SubscriptionInvoiceRead:
        inv = self.get_invoice(invoice_id)
        self.ensure_portal_invoice_access(portal_email, inv.shop_id)
        return inv

    def list_invoices_for_portal(
        self,
        portal_email: str,
        *,
        page: int,
        limit: int,
        filters: dict[str, Any],
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[list[SubscriptionInvoiceListItem], int]:
        shop_id = self.resolve_portal_shop_id(portal_email)
        if not shop_id:
            return [], 0
        merged = {**filters, "shop_id": shop_id}
        return self.list_invoices(page=page, limit=limit, filters=merged, order_by=order_by)

    def create_manual_invoice_for_portal(
        self, portal_email: str, payload: SubscriptionInvoiceCreate
    ) -> SubscriptionInvoiceRead:
        shop_id = self.resolve_portal_shop_id(portal_email)
        if not shop_id or shop_id != payload.shop_id:
            log.info(
                "create_manual_invoice portal denied",
                extra={"portal_email": portal_email, "payload_shop_id": getattr(payload, "shop_id", None)},
            )
            raise PermissionDeniedError("Not enough permissions")
        return self.create_manual_invoice(payload)

    def update_invoice_for_portal(
        self, portal_email: str, invoice_id: int, payload: SubscriptionInvoiceUpdate
    ) -> SubscriptionInvoiceRead:
        inv = self.get_invoice(invoice_id)
        self.ensure_portal_invoice_access(portal_email, inv.shop_id)
        return self.update_invoice(invoice_id, payload)

    def update_status_for_portal(
        self,
        portal_email: str,
        invoice_id: int,
        *,
        new_status: InvoiceStatus,
        paid_at: datetime | None = None,
        transaction_reference: str | None = None,
    ) -> SubscriptionInvoiceRead:
        inv = self.get_invoice(invoice_id)
        self.ensure_portal_invoice_access(portal_email, inv.shop_id)
        return self.update_status(
            invoice_id,
            new_status=new_status,
            paid_at=paid_at,
            transaction_reference=transaction_reference,
        )

    def retry_bill_for_portal(self, portal_email: str, invoice_id: int) -> SubscriptionInvoiceRead:
        inv = self.get_invoice(invoice_id)
        self.ensure_portal_invoice_access(portal_email, inv.shop_id)
        return self.retry_bill_generation(invoice_id)

    def list_invoices(
        self,
        *,
        page: int,
        limit: int,
        filters: dict[str, Any],
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[list[SubscriptionInvoiceListItem], int]:
        validate_page_and_limit_invoice(page, limit)

        rows, total = self.repository.list_invoices(page=page, limit=limit, filters=filters, order_by=order_by)
        items = [SubscriptionInvoiceListItem.model_validate(r) for r in rows]
        return items, total

    def get_invoice(self, invoice_id: int) -> SubscriptionInvoiceRead:
        validate_positive_id(invoice_id, field_name="invoice_id")
        invoice = self.repository.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found", code=ErrorCode.RESOURCE_NOT_FOUND)
        return SubscriptionInvoiceRead.model_validate(invoice)

    def _validate_amounts(self, payload: SubscriptionInvoiceCreate | SubscriptionInvoiceUpdate) -> None:
        data = payload.model_dump(exclude_unset=True)
        for key in ("amount", "discount", "other_charges", "cgst", "igst", "sgst"):
            if key in data and data[key] is not None:
                value = Decimal(str(data[key]))
                if value < 0:
                    raise DomainValidationError(f"{key} cannot be negative", code=ErrorCode.VALIDATION_ERROR)

    def create_manual_invoice(self, payload: SubscriptionInvoiceCreate) -> SubscriptionInvoiceRead:
        self._validate_amounts(payload)
        # Enforce uniqueness: one per shop + billing period start + type
        if self.repository.exists_for_shop_period_type(
            shop_id=payload.shop_id,
            billing_period_start=payload.billing_period_start,
            document_type=payload.document_type.value,
        ):
            raise ConflictError(
                "An invoice already exists for this shop, billing period, and document type",
                code=ErrorCode.CONFLICT,
            )
        # Invoice number is provided externally; keep old behavior for backfill/manuals
        with session_commit_scope(self._session):
            created = self.repository.create_invoice(payload)
        return SubscriptionInvoiceRead.model_validate(created)

    def _next_sequence(self, *, document_type: InvoiceDocumentType, now: datetime) -> int:
        prefix = "INV" if document_type == InvoiceDocumentType.INVOICE else "BILL"
        ym = now.strftime("%Y%m")
        best = self.repository.max_invoice_sequence_suffix(
            document_type=document_type,
            prefix=prefix,
            ym=ym,
        )
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
            raise ConflictError(
                "Document already exists for this shop and period",
                code=ErrorCode.CONFLICT,
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
            # Store notes as a JSON log, even for system-created invoices.
            object.__setattr__(payload, "notes", self._append_note_log(None, notes))
        self._validate_amounts(payload)
        with session_commit_scope(self._session):
            created = self.repository.create_invoice(payload)
        return SubscriptionInvoiceRead.model_validate(created)

    def update_invoice(self, invoice_id: int, payload: SubscriptionInvoiceUpdate) -> SubscriptionInvoiceRead:
        invoice = self._require_invoice(invoice_id)
        data = payload.model_dump(exclude_unset=True)
        # Protect invoice_number from updates
        if "invoice_number" in data:
            raise DomainValidationError(
                "invoice_number cannot be modified", code=ErrorCode.VALIDATION_ERROR
            )
        # Limit edits when PAID
        if invoice.status == InvoiceStatus.PAID:
            forbidden_keys = {"amount", "discount", "other_charges", "cgst", "igst", "sgst", "billing_period_start", "billing_period_end"}
            if any(k in data for k in forbidden_keys):
                raise BusinessRuleViolationError(
                    "Paid invoices have restricted editable fields",
                    code=ErrorCode.VALIDATION_ERROR,
                )
        # Normalize notes into a JSON log string (append or mark deleted).
        if "notes" in data:
            new_note = data.get("notes")
            if new_note is not None:
                note_str = str(new_note).strip()
                if note_str.startswith("__DELETE_NOTE_ID__:"):
                    note_id = note_str.split(":", 2)[-1].strip() or None
                    data["notes"] = self._mark_note_deleted(invoice.notes, note_id)
                    payload.notes = data["notes"]
                else:
                    data["notes"] = self._append_note_log(invoice.notes, note_str)
                    payload.notes = data["notes"]
            else:
                # Explicitly clearing notes keeps behaviour: allow null to blank out the log.
                payload.notes = None
        self._validate_amounts(payload)
        with session_commit_scope(self._session):
            updated = self.repository.update_invoice(invoice, payload)
        return SubscriptionInvoiceRead.model_validate(updated)

    def _append_note_log(self, existing: str | None, new_text: str) -> str:
        """
        Append a note entry to the existing JSON log stored in SubscriptionInvoice.notes.

        Format stored in DB (string, but valid JSON object):
        {
          "1": "Test 1 [2026-03-12 10:00:00 UTC]",
          "2": "Test 2 [2026-03-12 11:30:15 UTC]"
        }
        """
        text = (new_text or "").strip()
        if not text:
            # If nothing meaningful was provided, keep existing as-is.
            return existing or ""

        data: dict[str, str]
        if existing:
            try:
                parsed = json.loads(existing)
                if isinstance(parsed, dict):
                    # Ensure all keys are strings so json.dumps is stable.
                    data = {str(k): str(v) for k, v in parsed.items()}
                else:
                    data = {}
            except Exception:
                # If legacy/plain text is present, keep it under key "1" and start fresh.
                data = {}
                if existing.strip():
                    data["1"] = str(existing).strip()
        else:
            data = {}

        # Find the next numeric key.
        max_idx = 0
        for k in data.keys():
            try:
                n = int(str(k))
                if n > max_idx:
                    max_idx = n
            except ValueError:
                continue
        next_idx = max_idx + 1

        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        data[str(next_idx)] = f"{text} [{timestamp}]"

        return json.dumps(data, ensure_ascii=False)

    def _mark_note_deleted(self, existing: str | None, note_id: str | None) -> str:
        """
        Mark a specific note entry as deleted, keeping its key but replacing the value.

        Result example (for id \"3\"):
        {
          "3": "deleted [2026-03-12 10:00:00 UTC]"
        }
        """
        if not existing:
            return existing or ""
        try:
            parsed = json.loads(existing)
            if not isinstance(parsed, dict):
                return existing
        except Exception:
            return existing

        if not note_id:
            return existing

        key = str(note_id)
        if key not in parsed:
            return existing

        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        parsed[key] = f"deleted [{timestamp}]"

        return json.dumps({str(k): v for k, v in parsed.items()}, ensure_ascii=False)

    def _require_invoice(self, invoice_id: int) -> SubscriptionInvoice:
        validate_positive_id(invoice_id, field_name="invoice_id")
        invoice = self.repository.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found", code=ErrorCode.RESOURCE_NOT_FOUND)
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
                raise DomainValidationError(
                    "paid_at cannot be in the future", code=ErrorCode.VALIDATION_ERROR
                )
            if not transaction_reference:
                raise DomainValidationError(
                    "transaction_reference is required when marking invoice as PAID",
                    code=ErrorCode.VALIDATION_ERROR,
                )
            update_data["paid_at"] = paid_at
            update_data["transaction_reference"] = transaction_reference

        update_payload = SubscriptionInvoiceUpdate(**update_data)
        with session_commit_scope(self._session):
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
            raise BusinessRuleViolationError(
                "Bills cannot generate bills", code=ErrorCode.VALIDATION_ERROR
            )
        if invoice.status != InvoiceStatus.PAID:
            raise BusinessRuleViolationError(
                "Only PAID invoices can generate bills", code=ErrorCode.VALIDATION_ERROR
            )

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
            raise ConflictError("Bill already exists", code=ErrorCode.CONFLICT)

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
            except ConflictError:
                skipped += 1
                continue
        return {"generated": generated, "skipped": skipped}

    def run_overdue_automation(self) -> dict[str, int]:
        transitioned_to_pending = 0
        transitioned_to_overdue = 0
        now = datetime.now(timezone.utc)

        with session_commit_scope(self._session):
            # Rule: After the 5th of each month, any unpaid ISSUED invoices become PENDING.
            if now.day > 5:
                for invoice in self.repository.list_issued_invoices_for_current_month():
                    self.repository.update_invoice(
                        invoice,
                        SubscriptionInvoiceUpdate(status=InvoiceStatus.PENDING),
                    )
                    transitioned_to_pending += 1

            for invoice in self.repository.list_pending_invoices():
                next_invoice_date = (invoice.billing_period_start + timedelta(days=32)).replace(day=1)
                overdue_trigger = next_invoice_date - timedelta(days=5)
                if now >= overdue_trigger:
                    self.repository.update_invoice(
                        invoice,
                        SubscriptionInvoiceUpdate(status=InvoiceStatus.OVERDUE),
                    )
                    transitioned_to_overdue += 1
        return {
            "transitioned_to_pending": transitioned_to_pending,
            "transitioned_to_overdue": transitioned_to_overdue,
        }

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
        with session_commit_scope(self._session):
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
            with session_commit_scope(self._session):
                self.repository.create_invoice(payload)
            imported += 1
        return {"imported": imported, "skipped": skipped}

    def get_accounts_overview(self, *, days: int, shop_id: str | None = None) -> dict[str, Any]:
        validate_days_range(days, min_d=1, max_d=365)
        return self.repository.get_accounts_overview(days=days, shop_id=shop_id)

    def get_accounts_overview_for_portal(self, portal_email: str, *, days: int) -> dict[str, Any]:
        shop_id = self.resolve_portal_shop_id(portal_email)
        if not shop_id:
            return _empty_accounts_overview(days)
        return self.get_accounts_overview(days=days, shop_id=shop_id)

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
            raise BusinessRuleViolationError(
                f"Cannot transition invoice from {current.value} to {new.value}",
                code=ErrorCode.VALIDATION_ERROR,
            )

