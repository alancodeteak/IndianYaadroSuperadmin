from fastapi import APIRouter

router = APIRouter(tags=["internal"])


@router.get("/health")
async def health() -> dict:
    # Keep consistent contract even for internal endpoints.
    return {"data": {"status": "ok"}, "meta": None}

