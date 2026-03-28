from fastapi import APIRouter, Depends

from app.api.exceptions.error_codes import ErrorCode
from app.api.v1.schemas.auth import OTPResponse, ScopedSendOTPRequest, ScopedVerifyOTPRequest
from app.api.deps import get_auth_service
from app.services.auth_service import AuthService

router = APIRouter(prefix="/login", tags=["login"])


@router.post("/send-otp")
async def send_scoped_otp(
    payload: ScopedSendOTPRequest, service: AuthService = Depends(get_auth_service)
) -> dict:
    await service.send_otp(scope=payload.scope, email=payload.email)
    return {
        "data": OTPResponse(message="OTP sent successfully", code=ErrorCode.OTP_SENT).model_dump(),
        "meta": None,
    }


@router.post("/verify-otp")
def verify_scoped_otp(
    payload: ScopedVerifyOTPRequest, service: AuthService = Depends(get_auth_service)
) -> dict:
    session = service.verify_otp(
        scope=payload.scope,
        email=payload.email,
        otp_code=payload.otp_code,
    )
    return {
        "data": {
            "access_token": session.access_token,
            "token_type": session.token_type,
            "expires_at": session.expires_at.isoformat(),
            "role": session.role.value,
        },
        "meta": None,
    }
