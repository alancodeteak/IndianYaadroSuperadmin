from fastapi import APIRouter

router = APIRouter(prefix="/monitorapp", tags=["monitorapp"])


@router.get("/")
def monitorapp_root() -> dict:
    return {"data": {"message": "Monitor app API router ready"}, "meta": None}
