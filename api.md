# Yadro Superadmin API Generation Guide (Phase-by-Phase)

This document defines the recommended order to build and release APIs after completing auth (`/login`, `/auth`, `/portal` OTP flows).

**Last updated:** March 2026  
**Backend stack:** FastAPI + dependency-injected services + JWT + middleware-based security

---

## Current baseline (already done)

- OTP login APIs are available:
  - `POST /login/send-otp`
  - `POST /login/verify-otp`
  - Legacy compatibility:
    - `POST /auth/send-otp`, `POST /auth/verify-otp`, `POST /auth/logout`
    - `POST /portal/send-otp`, `POST /portal/verify-otp`, `POST /portal/logout`
- JWT session issue/revoke is implemented.
- Security middleware is active (request ID, logging, metrics, CORS, trusted hosts, security headers, rate limit, optional API-key checks).

Use this as the base for all next API phases.

---

## API generation principles (apply in every phase)

1. Build business logic in service/repository layers first, then expose routes.
2. Keep routers thin: request validation, dependency injection, response mapping only.
3. Reuse standard error envelope:
   - `{"error":{"code":"...","message":"...","request_id":"...","details":{}}}`
4. Protect non-public endpoints with JWT (`require_authenticated`).
5. Add focused tests for each new route (success + error + auth).
6. Update docs after each phase before moving to next.

---

## Standard checklist per new endpoint

For each endpoint you add, complete this in order:

1. **Schema**
   - Add request/response models under `app/api/v1/schemas/`.
2. **Service use case**
   - Add/extend method in `app/services/`.
3. **Repository/data access**
   - Add/extend repository method if DB access is needed.
4. **Dependency wiring**
   - Register provider in `app/api/deps/` when needed.
5. **Router endpoint**
   - Add route in proper module under `app/api/v1/routers/*/routes.py`.
6. **Protection**
   - Public only if explicitly required; otherwise JWT-protected.
7. **Tests**
   - Add route tests and service tests.
8. **Docs**
   - Update this file + `docs/frontend-auth-integration.md` when auth/frontend behavior changes.

---

## Phase 1 - Stabilize authentication surface

**Goal:** Finalize auth behavior before scaling business APIs.

### Scope

- Keep `/login/*` as primary API for frontend.
- Keep `/auth/*` and `/portal/*` as legacy compatibility only.
- Confirm all protected routers reject missing/invalid tokens with stable error codes.

### Deliverables

- Clear “recommended vs legacy” labels in docs.
- Test coverage for:
  - OTP sent, OTP invalid, OTP expired, attempts exceeded
  - logout token revocation (`AUTH_SESSION_EXPIRED`)
  - allowlist failures (`UNAUTHORIZED`)
- OTP debug logging only when `OTP_LOG_TO_TERMINAL=true`.

### Exit criteria

- Frontend team can complete login/logout flow end-to-end using only `/login/*`.

---

## Phase 2 - Dashboard + search + report APIs

**Goal:** Expose core operational APIs for authenticated users.

### Target routers

- `app/api/v1/routers/dashboard/routes.py`
- `app/api/v1/routers/search/routes.py`
- `app/api/v1/routers/report/routes.py`

### Scope

- List/dashboard summary endpoints
- Search endpoint(s) with pagination/filter schema
- Report generation trigger/download endpoints

### Security

- All endpoints JWT-protected via protected router.
- Apply API-key validation only for sensitive admin/metrics paths.

### Exit criteria

- Dashboard frontend can fetch summary, search, and reports with bearer token.

---

## Phase 3 - Orders + delivery partners + supermarkets

**Goal:** Deliver operational entity management APIs.

### Target routers

- `app/api/v1/routers/orders/routes.py`
- `app/api/v1/routers/delivery_partners/routes.py`
- `app/api/v1/routers/supermarkets*/routes.py` (grouped module as applicable)

### Scope

- CRUD/list/filter endpoints
- Status transitions (block/unblock/restore/etc.)
- Pagination and validation consistency

### Security

- JWT required for all write operations.
- Role checks where needed (superadmin-only actions).

### Exit criteria

- Authenticated users can manage orders, delivery partners, and supermarkets through documented APIs.

---

## Phase 4 - Analytics + daily activity + invoices

**Goal:** Add analytics/reporting-heavy APIs and finance APIs.

### Target routers

- `app/api/v1/routers/analytics/routes.py`
- `app/api/v1/routers/daily_activity/routes.py`
- `app/api/v1/routers/invoices/routes.py`

### Scope

- KPI/stat endpoints
- Daily activity data/export
- Invoice listing/details/status updates/downloads

### Security

- JWT mandatory.
- Additional API-key layer for metrics internals where required.

### Exit criteria

- Finance and analytics views fully powered by stable APIs.

---

## Phase 5 - Monitor app + hardening + observability

**Goal:** Final platform hardening before production rollout.

### Scope

- Monitor app endpoint stabilization (`app/api/v1/routers/monitorapp/routes.py`)
- Production toggles:
  - HTTPS redirect
  - trusted host allowlist
  - docs exposure policy
- Structured logging and latency metrics review
- Rate-limit tuning by endpoint group

### Exit criteria

- Production-ready security posture and predictable observability.

---

## Suggested release cadence

- Release per phase (small, testable increments).
- Do not merge next phase until:
  - tests pass
  - docs updated
  - frontend contract validated

---

## Security matrix (quick reference)

- **Public endpoints:** health, OTP send/verify, explicit compatibility routes only.
- **JWT endpoints:** all business/data APIs (dashboard/search/report/orders/etc.).
- **API key endpoints:** only selected admin/metrics internal paths.
- **Global middleware:** CORS, request ID, logging, metrics, rate limit, security headers, trusted host (and HTTPS redirect when enabled).

---

## Documentation maintenance rules

- Update this file whenever:
  - a new router/endpoint is added
  - auth requirement changes
  - request/response schema changes
  - error codes change
- Keep frontend-facing auth flow details in:
  - `docs/frontend-auth-integration.md`
