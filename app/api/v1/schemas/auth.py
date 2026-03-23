from datetime import datetime

from pydantic import BaseModel


class ScopedSendOTPRequest(BaseModel):
    scope: str
    email: str


class ScopedVerifyOTPRequest(BaseModel):
    scope: str
    email: str
    otp_code: str


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

