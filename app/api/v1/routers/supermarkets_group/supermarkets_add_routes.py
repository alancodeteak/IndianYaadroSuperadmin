from fastapi import APIRouter

router = APIRouter(prefix="/supermarkets/add", tags=["supermarkets-add"])


@router.get("/")
def supermarkets_add_root() -> dict:
    return {"data": {"message": "Supermarkets add API router ready"}, "meta": None}
