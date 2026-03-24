# Frontend Auth Integration Guide

This guide explains how the frontend at `http://localhost:5173` should integrate with authentication APIs.

## Base Information

- Backend base URL (local): `http://127.0.0.1:8000`
- Frontend origin allowed by CORS: `http://localhost:5173`
- Auth transport: Bearer JWT in `Authorization` header
- Error envelope format:
  - `{"error": {"code": "...", "message": "...", "request_id": "...", "details": {...}}}`

## Recommended API Surface (Use This First)

Use unified login APIs for new frontend work:

- `POST /login/send-otp`
- `POST /login/verify-otp`

Legacy APIs are still available for compatibility.

## Endpoint Matrix

### Unified (recommended)

1) `POST /login/send-otp`
- Request:
```json
{
  "scope": "admin",
  "email": "yaadro@codeteak.com"
}
```
- `scope` values:
  - `admin`
  - `portal`
- Success response:
```json
{
  "data": {
    "message": "OTP sent successfully",
    "code": "OTP_SENT"
  },
  "meta": null
}
```

2) `POST /login/verify-otp`
- Request:
```json
{
  "scope": "admin",
  "email": "yaadro@codeteak.com",
  "otp_code": "123456"
}
```
- Success response:
```json
{
  "data": {
    "access_token": "jwt-token",
    "token_type": "bearer",
    "expires_at": "2026-03-23T12:34:56+00:00",
    "role": "SUPERADMIN"
  },
  "meta": null
}
```

### Legacy Admin APIs

- `POST /auth/send-otp`
- `POST /auth/verify-otp`
- `POST /auth/logout`

### Legacy Portal APIs

- `POST /portal/send-otp`
- `POST /portal/verify-otp`
- `POST /portal/logout`

## Token Handling in Frontend

After `verify-otp` success:

1) Store token securely in memory-first strategy.
2) Add header on authenticated API calls:
   - `Authorization: Bearer <access_token>`
3) Track `expires_at` and force re-login on expiry.
4) On logout:
   - call logout endpoint
   - clear local token/session state

## Logout and Session Revocation

- Admin logout: `POST /auth/logout`
- Portal logout: `POST /portal/logout`
- Logout revokes current token `jti` server-side.
- Using revoked token later returns:
  - `401` with `AUTH_SESSION_EXPIRED`

## Error Codes Frontend Must Handle

Auth and OTP:
- `OTP_SENT` (success code in response payload)
- `OTP_INVALID`
- `OTP_EXPIRED`
- `OTP_ATTEMPTS_EXCEEDED`
- `OTP_RATE_LIMITED`
- `OTP_DELIVERY_FAILED`
- `UNAUTHENTICATED`
- `UNAUTHORIZED`
- `AUTH_SESSION_EXPIRED`
- `VALIDATION_ERROR`
- `REQUEST_VALIDATION_ERROR`

Generic:
- `INTERNAL_SERVER_ERROR`

## Suggested Frontend Flow

1) User enters email and chooses role/scope (`admin` or `portal`).
2) Frontend calls `POST /login/send-otp`.
3) User enters OTP.
4) Frontend calls `POST /login/verify-otp`.
5) Frontend stores token and role from response.
6) Frontend calls protected APIs with Bearer token.
7) On `401` with `AUTH_SESSION_EXPIRED` or `UNAUTHENTICATED`, redirect to login.

## Migration Strategy (Legacy -> Unified)

- Keep old UI logic working with `/auth/*` and `/portal/*`.
- For all new screens, use `/login/*`.
- Gradually move old flows to unified endpoints.

## CORS Notes

Current allowlist should include:
- `http://localhost:5173`

If frontend still sees CORS errors:
- verify backend restarted after env/config change
- check browser preflight response headers
- ensure frontend sends `Authorization` only when token exists

