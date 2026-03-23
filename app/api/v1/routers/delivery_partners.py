from fastapi import APIRouter

router = APIRouter(prefix="/delivery-partners", tags=["delivery-partners"])


@router.get("/")
async def list_delivery_partners() -> dict:
    return {"data": {"message": "Delivery partners API router ready"}, "meta": None}

