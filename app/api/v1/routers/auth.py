from fastapi import APIRouter, Depends

from app.api.deps import require_authenticated

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login_page() -> dict:
    return {"data": {"message": "Not implemented yet"}, "meta": None}


@router.post("/send-otp")
async def send_otp() -> dict:
    return {"data": {"message": "Not implemented yet"}, "meta": None}


@router.post("/verify-otp")
async def verify_otp() -> dict:
    return {"data": {"message": "Not implemented yet"}, "meta": None}


@router.post("/logout")
async def logout(_: object = Depends(require_authenticated)) -> dict:
    return {"data": {"message": "Not implemented yet"}, "meta": None}

