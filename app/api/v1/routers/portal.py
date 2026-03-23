from fastapi import APIRouter

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/")
async def portal_root() -> dict:
    return {"data": {"message": "Portal API router ready"}, "meta": None}

