from fastapi import APIRouter

router = APIRouter(prefix="/api/report", tags=["report"])


@router.post("/")
def generate_report() -> dict:
    return {"data": {"message": "Report API router ready"}, "meta": None}
