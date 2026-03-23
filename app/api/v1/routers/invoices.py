from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin/invoices", tags=["invoices"])


@router.get("/")
async def list_invoices() -> dict:
    return {"data": {"message": "Invoices API router ready"}, "meta": None}

