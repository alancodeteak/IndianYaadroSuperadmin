from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/data")
async def dashboard_data() -> dict:
    return {"data": {"message": "Dashboard API router ready"}, "meta": None}

