from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.api.core.logger import get_logger
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.shop_owner_repository import ShopOwnerRepository
from app.services.invoice_service import InvoiceService

log = get_logger(__name__)


def _invoice_service(db: Session) -> InvoiceService:
    return InvoiceService(
        repository=InvoiceRepository(db=db),
        session=db,
        shop_owner_repository=ShopOwnerRepository(db=db),
    )


def run_monthly_invoice_generation_job(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    service = _invoice_service(db)
    result = service.generate_monthly(year=now.year, month=now.month)
    log.info("run_monthly_invoice_generation_job", extra=result)
    return result


def run_status_automation_job(db: Session) -> dict:
    service = _invoice_service(db)
    result = service.run_overdue_automation()
    log.info("run_status_automation_job", extra=result)
    return result


def run_bill_retry_job(db: Session, invoice_ids: list[int]) -> dict:
    service = _invoice_service(db)
    retried = 0
    failed = 0
    for invoice_id in invoice_ids:
        try:
            service.retry_bill_generation(invoice_id)
            retried += 1
        except Exception:
            failed += 1
    result = {"retried": retried, "failed": failed}
    log.info("run_bill_retry_job", extra=result)
    return result


def run_notes_sync_job(db: Session, invoice_ids: list[int]) -> dict:
    service = _invoice_service(db)
    synced = 0
    for invoice_id in invoice_ids:
        result = service.sync_notes_between_invoice_and_bill(invoice_id)
        synced += int(result.get("synced", 0))
    output = {"synced": synced}
    log.info("run_notes_sync_job", extra=output)
    return output

