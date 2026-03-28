from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_order_service, require_authenticated
from app.api.deps.auth import CurrentUser
from app.api.v1.schemas.order import OrderCreate, OrderListItem, OrderRead, OrderUpdate
from app.services.order_service import OrderService

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["orders"],
)


@router.get("/", response_model=dict)
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_authenticated),
    service: OrderService = Depends(get_order_service),
):
    rows, total = service.list_orders(
        role=current_user.role,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )
    return {
        "data": [OrderListItem.model_validate(row).model_dump() for row in rows],
        "meta": {
            "page": page,
            "pageSize": page_size,
            "total": total,
        },
    }


@router.get("/{order_id}", response_model=dict)
def get_order(
    order_id: int,
    current_user: CurrentUser = Depends(require_authenticated),
    service: OrderService = Depends(get_order_service),
):
    row = service.get_order(
        role=current_user.role, user_id=current_user.user_id, order_id=order_id
    )
    return {"data": OrderRead.model_validate(row).model_dump(), "meta": None}


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_order(
    payload: OrderCreate,
    current_user: CurrentUser = Depends(require_authenticated),
    service: OrderService = Depends(get_order_service),
):
    created = service.create_order(
        role=current_user.role, user_id=current_user.user_id, payload=payload
    )
    return {"data": OrderRead.model_validate(created).model_dump(), "meta": None}


@router.patch("/{order_id}", response_model=dict)
def patch_order(
    order_id: int,
    payload: OrderUpdate,
    current_user: CurrentUser = Depends(require_authenticated),
    service: OrderService = Depends(get_order_service),
):
    updated = service.update_order(
        role=current_user.role,
        user_id=current_user.user_id,
        order_id=order_id,
        payload=payload,
    )
    return {"data": OrderRead.model_validate(updated).model_dump(), "meta": None}
