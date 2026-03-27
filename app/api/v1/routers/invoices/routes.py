from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps.auth import CurrentUser, require_roles
from app.api.deps.services import get_invoice_service
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.subscription_invoice import (
    SubscriptionInvoiceCreate,
    SubscriptionInvoiceListItem,
    SubscriptionInvoiceRead,
    SubscriptionInvoiceUpdate,
)
from app.domain.enums.roles import Role
from app.infrastructure.db.models.enums import InvoiceDocumentType, InvoiceStatus
from app.services.invoice_service import InvoiceService


router = APIRouter(prefix="/api/v1/admin/invoices", tags=["invoices"])


class LegacyImportPayload(BaseModel):
    rows: list[dict[str, Any]]


@router.get(
    "",
    response_model=dict[str, Any],
)
async def list_invoices_admin(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
    shop_id: str | None = None,
    status: InvoiceStatus | None = None,
    document_type: InvoiceDocumentType | None = None,
    subscription_id: int | None = None,
    billing_period_start: datetime | None = None,
    billing_period_end: datetime | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    search: str | None = None,
    sort: str | None = Query(default="-billing_period_start"),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user  # role already validated
    filters: dict[str, Any] = {
        "shop_id": shop_id,
        "status": status,
        "document_type": document_type,
        "subscription_id": subscription_id,
        "billing_period_start": billing_period_start,
        "billing_period_end": billing_period_end,
        "created_from": created_from,
        "created_to": created_to,
        "search": search,
    }
    order_by: list[tuple[str, str]] = []
    if sort:
        for part in sort.split(","):
            part = part.strip()
            if not part:
                continue
            direction = "asc"
            field = part
            if part.startswith("-"):
                direction = "desc"
                field = part[1:]
            order_by.append((field, direction))
    items, total = service.list_invoices(page=page, limit=limit, filters=filters, order_by=order_by)
    return {
        "data": [item.model_dump() for item in items],
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.get(
    "/{invoice_id}",
    response_model=dict[str, Any],
)
async def get_invoice_admin(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    invoice = service.get_invoice(invoice_id)
    return {"data": invoice.model_dump(), "meta": None}


@router.post(
    "/create-manual",
    response_model=dict[str, Any],
)
async def create_manual_invoice_admin(
    payload: SubscriptionInvoiceCreate,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    invoice = service.create_manual_invoice(payload)
    return {"data": invoice.model_dump(), "meta": None}


@router.put(
    "/{invoice_id}",
    response_model=dict[str, Any],
)
async def update_invoice_admin(
    invoice_id: int,
    payload: SubscriptionInvoiceUpdate,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    invoice = service.update_invoice(invoice_id, payload)
    return {"data": invoice.model_dump(), "meta": None}


@router.patch(
    "/{invoice_id}/status",
    response_model=dict[str, Any],
)
async def update_invoice_status_admin(
    invoice_id: int,
    new_status: InvoiceStatus,
    paid_at: datetime | None = None,
    transaction_reference: str | None = None,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    invoice = service.update_status(
        invoice_id,
        new_status=new_status,
        paid_at=paid_at,
        transaction_reference=transaction_reference,
    )
    return {"data": invoice.model_dump(), "meta": None}


@router.get(
    "/monthly-summary",
    response_model=dict[str, Any],
)
async def monthly_summary_admin(
    year: int,
    month: int,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    summary = service.repository.monthly_summary(year=year, month=month)
    return {"data": summary, "meta": {"year": year, "month": month}}


@router.post("/generate-monthly", response_model=dict[str, Any])
async def generate_monthly_now_admin(
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    now = datetime.utcnow()
    result = service.generate_monthly(year=now.year, month=now.month)
    return {"data": result, "meta": None}


@router.post("/generate-monthly-for-month", response_model=dict[str, Any])
async def generate_monthly_for_month_admin(
    year: int,
    month: int,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    if month < 1 or month > 12:
        raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="month must be 1-12", status_code=400)
    return {"data": service.generate_monthly(year=year, month=month), "meta": None}


@router.post("/run-status-automation", response_model=dict[str, Any])
async def run_status_automation_admin(
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    return {"data": service.run_overdue_automation(), "meta": None}


@router.post("/{invoice_id}/retry-bill", response_model=dict[str, Any])
async def retry_bill_admin(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    bill = service.retry_bill_generation(invoice_id)
    return {"data": bill.model_dump(), "meta": None}


@router.post(
    "/{invoice_id}/send-email",
    response_model=dict[str, Any],
)
async def send_invoice_email_admin(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
) -> dict[str, Any]:
    del current_user
    # Placeholder implementation; actual email integration to be added later.
    if invoice_id <= 0:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="invoice_id must be > 0",
            status_code=400,
        )
    return {"data": {"code": "EMAIL_NOT_CONFIGURED"}, "meta": None}


@router.post("/import-legacy", response_model=dict[str, Any])
async def import_legacy_admin(
    payload: LegacyImportPayload,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    del current_user
    result = service.import_legacy_documents(payload.rows)
    return {"data": result, "meta": None}


@router.post(
    "/{invoice_id}/send-followup-email",
    response_model=dict[str, Any],
)
async def send_invoice_followup_email_admin(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
) -> dict[str, Any]:
    del current_user
    if invoice_id <= 0:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="invoice_id must be > 0",
            status_code=400,
        )
    return {"data": {"code": "EMAIL_NOT_CONFIGURED"}, "meta": None}


@router.get(
    "/{invoice_id}/download",
    response_model=dict[str, Any],
)
async def download_invoice_admin(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
) -> dict[str, Any]:
    del current_user
    if invoice_id <= 0:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="invoice_id must be > 0",
            status_code=400,
        )
    return {
        "data": {
            "code": "PDF_NOT_CONFIGURED",
            "message": "Invoice PDF template is not configured yet",
            "invoice_id": invoice_id,
        },
        "meta": None,
    }


portal_router = APIRouter(prefix="/api/v1/portal/invoices", tags=["portal-invoices"])


@portal_router.get("", response_model=dict[str, Any])
async def list_invoices_portal(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    items, total = service.list_invoices(
        page=page,
        limit=limit,
        filters={"shop_id": current_user.user_id},
        order_by=[("billing_period_start", "desc")],
    )
    return {"data": [i.model_dump() for i in items], "meta": {"page": page, "limit": limit, "total": total}}


@portal_router.get("/{invoice_id}", response_model=dict[str, Any])
async def get_invoice_portal(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    invoice = service.get_invoice(invoice_id)
    if invoice.shop_id != current_user.user_id:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    return {"data": invoice.model_dump(), "meta": None}


@portal_router.get("/{invoice_id}/download", response_model=dict[str, Any])
async def download_invoice_portal(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    invoice = service.get_invoice(invoice_id)
    if invoice.shop_id != current_user.user_id:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    return {
        "data": {
            "code": "PDF_NOT_CONFIGURED",
            "message": "Invoice PDF template is not configured yet",
            "invoice_id": invoice_id,
        },
        "meta": None,
    }


@portal_router.post("/create-manual", response_model=dict[str, Any])
async def create_manual_invoice_portal(
    payload: SubscriptionInvoiceCreate,
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    if payload.shop_id != current_user.user_id:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    invoice = service.create_manual_invoice(payload)
    return {"data": invoice.model_dump(), "meta": None}


@portal_router.put("/{invoice_id}", response_model=dict[str, Any])
async def update_invoice_portal(
    invoice_id: int,
    payload: SubscriptionInvoiceUpdate,
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    invoice = service.get_invoice(invoice_id)
    if invoice.shop_id != current_user.user_id:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    updated = service.update_invoice(invoice_id, payload)
    return {"data": updated.model_dump(), "meta": None}


@portal_router.patch("/{invoice_id}/status", response_model=dict[str, Any])
async def update_invoice_status_portal(
    invoice_id: int,
    new_status: InvoiceStatus,
    paid_at: datetime | None = None,
    transaction_reference: str | None = None,
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    invoice = service.get_invoice(invoice_id)
    if invoice.shop_id != current_user.user_id:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    updated = service.update_status(
        invoice_id,
        new_status=new_status,
        paid_at=paid_at,
        transaction_reference=transaction_reference,
    )
    return {"data": updated.model_dump(), "meta": None}


@portal_router.post("/{invoice_id}/retry-bill", response_model=dict[str, Any])
async def retry_bill_portal(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    invoice = service.get_invoice(invoice_id)
    if invoice.shop_id != current_user.user_id:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    bill = service.retry_bill_generation(invoice_id)
    return {"data": bill.model_dump(), "meta": None}


@portal_router.post("/{invoice_id}/send-email", response_model=dict[str, Any])
async def send_invoice_email_portal(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    invoice = service.get_invoice(invoice_id)
    if invoice.shop_id != current_user.user_id:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    return {"data": {"code": "EMAIL_NOT_CONFIGURED"}, "meta": None}


@portal_router.post("/{invoice_id}/send-followup-email", response_model=dict[str, Any])
async def send_followup_email_portal(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_roles(Role.PORTAL_USER)),
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, Any]:
    invoice = service.get_invoice(invoice_id)
    if invoice.shop_id != current_user.user_id:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    return {"data": {"code": "EMAIL_NOT_CONFIGURED"}, "meta": None}

