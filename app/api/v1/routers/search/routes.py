from fastapi import APIRouter

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/")
def search_all() -> dict:
    return {"data": {"message": "Search API router ready"}, "meta": None}
