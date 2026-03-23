"""Versioned API schemas."""

from app.api.v1.schemas.auth import (
    AuthTokenData,
    OTPResponse,
    ScopedSendOTPRequest,
    ScopedVerifyOTPRequest,
    SendOTPRequest,
    VerifyOTPRequest,
)

__all__ = [
    "SendOTPRequest",
    "VerifyOTPRequest",
    "ScopedSendOTPRequest",
    "ScopedVerifyOTPRequest",
    "OTPResponse",
    "AuthTokenData",
]

