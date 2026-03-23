from datetime import datetime

from pydantic import BaseModel


class SendOTPRequest(BaseModel):
    email: str


class VerifyOTPRequest(BaseModel):
    email: str
    otp_code: str


class OTPResponse(BaseModel):
    message: str
    code: str


class AuthTokenData(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    role: str

