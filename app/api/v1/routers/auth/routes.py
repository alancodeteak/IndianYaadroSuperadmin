from typing import Optional

from fastapi import APIRouter, Depends, Header

from app.api.deps import get_auth_service
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.auth import OTPResponse, SendOTPRequest, VerifyOTPRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login_page() -> dict:
    return {"data": {"message": "Not implemented yet"}, "meta": None}


@router.post("/send-otp")
async def send_otp(payload: SendOTPRequest, service: AuthService = Depends(get_auth_service)) -> dict:
    service.send_admin_otp(email=str(payload.email))
    return {
        "data": OTPResponse(message="OTP sent successfully", code=ErrorCode.OTP_SENT).model_dump(),
        "meta": None,
    }


@router.post("/verify-otp")
async def verify_otp(
    payload: VerifyOTPRequest, service: AuthService = Depends(get_auth_service)
) -> dict:
    session = service.verify_admin_otp(email=str(payload.email), otp_code=payload.otp_code)
    return {
        "data": {
            "access_token": session.access_token,
            "token_type": session.token_type,
            "expires_at": session.expires_at.isoformat(),
            "role": session.role.value,
        },
        "meta": None,
    }


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    token = _extract_bearer_token(authorization)
    service.logout(token)
    return {"data": {"message": "Logged out successfully"}, "meta": None}


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise ApiError(code=ErrorCode.UNAUTHENTICATED, message="Missing Authorization header", status_code=401)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ApiError(
            code=ErrorCode.UNAUTHENTICATED,
            message="Invalid Authorization header format",
            status_code=401,
        )
    return parts[1]
