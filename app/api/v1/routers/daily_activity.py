from fastapi import APIRouter

router = APIRouter(prefix="/daily-activity", tags=["daily-activity"])


@router.get("/")
async def daily_activity_root() -> dict:
    return {"data": {"message": "Daily activity API router ready"}, "meta": None}

