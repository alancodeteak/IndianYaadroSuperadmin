"""Versioned API schemas."""

from app.api.v1.schemas.auth import AuthTokenData, OTPResponse, SendOTPRequest, VerifyOTPRequest

__all__ = ["SendOTPRequest", "VerifyOTPRequest", "OTPResponse", "AuthTokenData"]

