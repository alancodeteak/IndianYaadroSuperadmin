from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.auth import CurrentUser, require_roles
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.domain.enums.roles import Role
from app.infrastructure.db.models.order import Order
from app.infrastructure.db.models.shop_owner import ShopOwner
from app.infrastructure.db.models.subscription_invoice import SubscriptionInvoice
from app.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/api/v1/admin/activity", tags=["activity"])


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


@router.get("/recent", response_model=dict[str, Any])
def list_recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    db: Session = Depends(get_db_session),
) -> dict[str, Any]:
    del current_user

    # Recent shop logins (best-effort: relies on ShopOwner.last_login_at being set).
    shop_rows = db.execute(
        select(
            ShopOwner.shop_id,
            ShopOwner.user_id,
            ShopOwner.shop_name,
            ShopOwner.last_login_at,
        )
        .where(
            ShopOwner.is_supermarket.is_(True),
            ShopOwner.is_deleted.is_(False),
            ShopOwner.last_login_at.is_not(None),
        )
        .order_by(ShopOwner.last_login_at.desc())
        .limit(limit)
    ).all()

    # Recent orders (created).
    order_rows = db.execute(
        select(
            Order.order_id,
            Order.shop_id,
            Order.created_at,
            Order.order_status,
            Order.total_amount,
        )
        .where(Order.is_deleted.is_(False))
        .order_by(Order.created_at.desc())
        .limit(limit)
    ).all()

    # Recent invoices (created + paid events).
    inv_rows = db.execute(
        select(
            SubscriptionInvoice.invoice_id,
            SubscriptionInvoice.shop_id,
            SubscriptionInvoice.invoice_number,
            SubscriptionInvoice.status,
            SubscriptionInvoice.created_at,
            SubscriptionInvoice.paid_at,
            SubscriptionInvoice.amount,
        )
        .order_by(SubscriptionInvoice.created_at.desc())
        .limit(limit)
    ).all()

    items: list[dict[str, Any]] = []

    for r in shop_rows:
        items.append(
            {
                "id": f"shop_login:{r.shop_id}:{_iso(r.last_login_at)}",
                "type": "SHOP_LOGIN",
                "occurred_at": _iso(r.last_login_at),
                "title": f"{r.shop_name} logged in",
                "shop": {"shop_id": r.shop_id, "user_id": r.user_id, "shop_name": r.shop_name},
                "meta": {},
            }
        )

    for r in order_rows:
        items.append(
            {
                "id": f"order_created:{r.order_id}",
                "type": "ORDER_CREATED",
                "occurred_at": _iso(r.created_at),
                "title": f"Order #{r.order_id} created",
                "shop": {"shop_id": r.shop_id},
                "meta": {
                    "order_id": r.order_id,
                    "order_status": str(r.order_status),
                    "amount": float(r.total_amount or 0),
                },
            }
        )

    for r in inv_rows:
        items.append(
            {
                "id": f"invoice_created:{r.invoice_id}",
                "type": "INVOICE_CREATED",
                "occurred_at": _iso(r.created_at),
                "title": f"Invoice {r.invoice_number} created",
                "shop": {"shop_id": r.shop_id},
                "meta": {
                    "invoice_id": r.invoice_id,
                    "invoice_number": r.invoice_number,
                    "status": str(r.status),
                    "amount": float(r.amount or 0),
                },
            }
        )
        if r.paid_at is not None:
            items.append(
                {
                    "id": f"invoice_paid:{r.invoice_id}",
                    "type": "INVOICE_PAID",
                    "occurred_at": _iso(r.paid_at),
                    "title": f"Invoice {r.invoice_number} paid",
                    "shop": {"shop_id": r.shop_id},
                    "meta": {
                        "invoice_id": r.invoice_id,
                        "invoice_number": r.invoice_number,
                        "status": str(r.status),
                        "amount": float(r.amount or 0),
                    },
                }
            )

    # Merge and sort by occurred_at desc; drop items without a timestamp.
    items = [it for it in items if it.get("occurred_at")]
    items.sort(key=lambda it: str(it.get("occurred_at")), reverse=True)
    items = items[:limit]

    if not items:
        # Keep response stable; frontend can show empty state.
        return {"data": [], "meta": {"limit": limit}}

    return {"data": items, "meta": {"limit": limit}}

