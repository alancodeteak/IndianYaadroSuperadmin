from fastapi import APIRouter

router = APIRouter(prefix="/supermarkets", tags=["supermarkets"])


@router.get("/")
async def list_supermarkets() -> dict:
    return {"data": {"message": "Supermarkets API router ready"}, "meta": None}

