# Delivery Partners API (Frontend Integration)

## Overview

- **Base URL**: your backend host (e.g. `http://127.0.0.1:8000`)
- **Auth**: Bearer JWT
  - Send header: `Authorization: Bearer <access_token>`
- **Roles**
  - **List + Search + Detail + Block + Delete**: `SUPERADMIN` only

## Standard response envelope

### Success

```json
{
  "data": {},
  "meta": null
}
```

### Error

```json
{
  "error": {
    "code": "SOME_CODE",
    "message": "Human readable message",
    "details": {},
    "request_id": "optional-request-id"
  }
}
```

Notes:
- `details` and `request_id` are optional.
- `code` is designed for frontend handling (switch/case).

## Common error codes

- **`UNAUTHENTICATED` (401)**: missing/invalid token
- **`UNAUTHORIZED` (403)**: token valid but role not allowed
- **`REQUEST_VALIDATION_ERROR` (400)**: request validation failed (FastAPI/Pydantic query parsing)
- **`VALIDATION_ERROR` (400)**: backend validation (e.g., empty id)
- **`RESOURCE_NOT_FOUND` (404)**: delivery partner not found or soft-deleted

---

## GET `/delivery-partners/` — List / Search Delivery Partners (Card)

**Auth**: `SUPERADMIN` only

### Query params

Required:
- `page` (int, default `1`, min `1`)
- `limit` (int, default `20`, min `1`, max `100`)

Optional filters (can combine):
- `name` (string) — partial, case-insensitive match against full name (`first_name` + `last_name`)
- `delivery_partner_id` (string) — exact match
- `shop_id` (string) — exact match
- `shop_name` (string) — partial, case-insensitive match on shop name
- `phone` (string) — exact match against `phone1` (digits only recommended)
- `current_status` (string) — exact match (example values: `idle`, `order_assigned`, `ongoing`)
- `online_status` (string) — exact match (example values: `online`, `offline`)

### Response

- `data`: `DeliveryPartnerCard[]`
- `meta`: pagination object

`DeliveryPartnerCard`:
- `delivery_partner_id` (string)
- `shop_id` (string)
- `shop_name` (string | null)
- `name` (string) — combined name for UI
- `phone` (string) — from `phone1` (string to avoid JS bigint issues)
- `photo` (string | null) — raw stored value (often an S3 key)
- `photo_url` (string | null) — usable URL (presigned if configured), otherwise `null`

`meta`:
- `currentPage` (int)
- `limit` (int)
- `total` (int)
- `totalPages` (int)

### Example request

```http
GET /delivery-partners?page=1&limit=20&shop_name=dmart&current_status=idle&online_status=online
Authorization: Bearer <access_token>
```

### Example success response

```json
{
  "data": [
    {
      "delivery_partner_id": "DP001",
      "shop_id": "SHOP001",
      "shop_name": "Dmart",
      "name": "John Doe",
      "phone": "919090999999",
      "photo": "delivery_partners/DP001/photo.jpg",
      "photo_url": "https://example.com/photo.jpg"
    }
  ],
  "meta": {
    "currentPage": 1,
    "limit": 20,
    "total": 1,
    "totalPages": 1
  }
}
```

### Errors

- `401 UNAUTHENTICATED`: missing/invalid token
- `403 UNAUTHORIZED`: not `SUPERADMIN`

---

## GET `/delivery-partners/{delivery_partner_id}` — Delivery Partner Detail

**Auth**: `SUPERADMIN` only

### Path param

- `delivery_partner_id` (string) — e.g. `DP001`

### Response

Returns the delivery partner detail object (all model fields **except secrets**) plus shop name.

Important:
- `password` is **not returned**
- `hmac_secret` is **not returned**
- `phone1`/`phone2` are returned as **strings**
- `photo_url` is provided when possible (presigned)

### Example request

```http
GET /delivery-partners/DP001
Authorization: Bearer <access_token>
```

### Example success response

```json
{
  "data": {
    "delivery_partner_id": "DP001",
    "shop_id": "SHOP001",
    "shop_name": "Dmart",
    "first_name": "John",
    "last_name": "Doe",
    "license_no": "LIC001",
    "license_image": "s3://license-image-key-or-url",
    "govt_id_image": null,
    "join_date": "2026-01-01T00:00:00+00:00",
    "is_blocked": false,
    "current_status": "idle",
    "order_count": 0,
    "age": 25,
    "phone1": "919090999999",
    "phone2": null,
    "email": null,
    "online_status": "offline",
    "rating": null,
    "photo": "delivery_partners/DP001/photo.jpg",
    "photo_url": "https://example.com/photo.jpg",
    "device_token": null,
    "device_id": null,
    "last_login": null,
    "last_order": null,
    "vehicle_detail": null,
    "total_bonus": 0,
    "total_penalty": 0,
    "liquid_cash": "0",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
    "is_deleted": false
  },
  "meta": null
}
```

### Errors

- `401 UNAUTHENTICATED`: missing/invalid token
- `403 UNAUTHORIZED`: not `SUPERADMIN`
- `404 RESOURCE_NOT_FOUND`: delivery partner id does not exist or is soft-deleted

---

## PATCH `/delivery-partners/{delivery_partner_id}/block` — Block / Unblock Delivery Partner

**Auth**: `SUPERADMIN` only

### Path param

- `delivery_partner_id` (string)

### Request body

```json
{ "blocked": true }
```

### Example request

```http
PATCH /delivery-partners/DP001/block
Authorization: Bearer <access_token>
Content-Type: application/json

{ "blocked": true }
```

### Example success response

```json
{
  "data": { "delivery_partner_id": "DP001", "is_blocked": true },
  "meta": null
}
```

### Errors

- `401 UNAUTHENTICATED`: missing/invalid token
- `403 UNAUTHORIZED`: not `SUPERADMIN`
- `404 RESOURCE_NOT_FOUND`: delivery partner id does not exist or is soft-deleted

---

## DELETE `/delivery-partners/{delivery_partner_id}` — Delete Delivery Partner (Soft Delete)

**Auth**: `SUPERADMIN` only

### Behavior

- Sets `delivery_partners.is_deleted = true`

### Example request

```http
DELETE /delivery-partners/DP001
Authorization: Bearer <access_token>
```

### Example success response

```json
{
  "data": { "delivery_partner_id": "DP001", "deleted": true },
  "meta": null
}
```

### Errors

- `401 UNAUTHENTICATED`: missing/invalid token
- `403 UNAUTHORIZED`: not `SUPERADMIN`
- `404 RESOURCE_NOT_FOUND`: delivery partner id does not exist or is soft-deleted

