from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/")
async def analytics_root() -> dict:
    return {"data": {"message": "Analytics API router ready"}, "meta": None}

