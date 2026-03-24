from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service
from app.api.exceptions.error_codes import ErrorCode
from app.api.v1.schemas.auth import OTPResponse, SendOTPRequest, VerifyOTPRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/portal", tags=["portal"])


@router.post("/send-otp")
async def send_portal_otp(
    payload: SendOTPRequest, service: AuthService = Depends(get_auth_service)
) -> dict:
    await service.send_portal_otp(email=str(payload.email))
    return {
        "data": OTPResponse(message="OTP sent successfully", code=ErrorCode.OTP_SENT).model_dump(),
        "meta": None,
    }


@router.post("/verify-otp")
async def verify_portal_otp(
    payload: VerifyOTPRequest, service: AuthService = Depends(get_auth_service)
) -> dict:
    session = service.verify_portal_otp(email=str(payload.email), otp_code=payload.otp_code)
    return {
        "data": {
            "access_token": session.access_token,
            "token_type": session.token_type,
            "expires_at": session.expires_at.isoformat(),
            "role": session.role.value,
        },
        "meta": None,
    }


