# Yadro Superadmin - Decoupled Backend/Frontend Blueprint

## What this is
This document describes how to build a new backend (API-only) and a separate frontend (SPA or SSR) from the current `yadro_superadmin-main` project.

The current codebase mixes server-rendered pages (EJS) with Express route handlers. The goal of this blueprint is to extract/standardize the backend into a pure HTTP API and let the frontend render all UI using the API.

The API contract (all current routes) is based on the Express routers under `src/routers/*.route.js` and is summarized in:
`docs/API_REFERENCE.md`

---

## Target architecture
Recommended split:
1. **Backend (API-only service)**
   - Node.js + Express (or NestJS/Fastify if you prefer, but keep behavior consistent)
   - Exposes JSON APIs and file export downloads (CSV/PDF)
   - Handles authentication, authorization, validation, database access, and exports
2. **Frontend (separate app)**
   - React / Next.js / Vue / Angular (any is fine)
   - Talks to the backend via `fetch`/Axios
   - Implements client-side routing, forms, tables, and downloads

Suggested deployment:
- Put both behind a reverse proxy (Nginx / Traefik) with CORS enabled from frontend to backend.
- Keep cookies/JWT secure, use HTTPS in production.

---

## Backend responsibilities (what moves to the API)
Extract the following responsibilities from the current server-rendered app:
1. **Auth**
   - Superadmin login/logout/OTP verification
   - Portal login/logout/OTP verification
2. **Portal and Dashboard data**
   - Data needed for dashboard tables/charts and portal pages
   - Any “export” endpoints (CSV/PDF) become download endpoints
3. **Core domain actions**
   - Delivery partners CRUD + block/unblock
   - Supermarkets CRUD + delete/restore + subscriptions
   - Orders filters for dashboard
4. **Invoices**
   - List invoices and retrieve invoice details
   - Generate bills/invoices with automations
   - Issue invoices, send emails, manage notes
5. **Analytics and daily activity**
   - Dashboard analytics data endpoints
   - Daily activity data endpoints
6. **System/metrics**
   - Cache rebuild/stats
   - Socket stats/metrics detailed views

What does NOT need to remain in backend:
- Rendering HTML pages (EJS templates)
- UI logic
- Frontend navigation/menus

---

## API design guidelines (recommended)
To make the new backend clean and frontend-friendly:
1. **Consistent response shape**
   - Success: `{ "data": ..., "meta": ... }`
   - Error: `{ "error": { "code": "X", "message": "..." } }`
2. **Use standard HTTP status codes**
   - 200/201/204 for success
   - 400 for validation errors
   - 401 for unauthenticated
   - 403 for unauthorized
   - 404 for not found
   - 409 for conflicts (e.g., duplicates)
   - 429 for rate limiting
   - 500 for server errors
3. **Validation**
   - Validate inputs with a schema library (e.g., Joi/Zod/class-validator)
4. **Pagination and filtering**
   - For list endpoints, prefer `?page=&pageSize=` and explicit filters
5. **File downloads**
   - Exports should set:
     - `Content-Type`
     - `Content-Disposition: attachment; filename="..."`
     - Return binary file streams (no base64 in JSON)
6. **CORS**
   - Allow only your frontend origin(s)

---

## Authentication and authorization strategy
The current project uses middleware such as:
- `isAuthenticated`
- `isPortalAuthenticated` / `isPortalNotAuthenticated`
- `isAuthenticatedOrPortal`
- `validateAdminApiKey` (admin-only API key actions)
- `validateMetricsApiKey` (metrics-only API key actions)
- `isMonitorAuthenticated`

When decoupling, choose one consistent approach:

### Option A: Session cookies (recommended if you want minimal backend changes)
- Keep `express-session` on backend.
- Frontend sends cookies automatically (`credentials: "include"`).
- Pros: fewer changes to server logic.
- Cons: requires careful CSRF protection.

### Option B: JWT (recommended for clean separation)
- Backend issues access JWT after OTP verification.
- Frontend stores access token in memory (or uses HttpOnly cookies).
- Pros: stateless APIs.
- Cons: needs refresh token and rotation strategy.

In either case:
1. Define role-based access:
   - `SUPERADMIN`
   - `PORTAL_USER`
   - `MONITOR_APP`
2. Keep existing access intent:
   - Portal endpoints under `/portal/*`
   - Invoice endpoints under `/api/v1/admin/invoices/*` shared by superadmin and portal as per middleware behavior
3. For admin/metrics API key endpoints:
   - Keep the dedicated API key middleware and document required headers (e.g., `x-api-key`)

---

## API contract (routes you must implement)
This blueprint expects the new API to support the routes documented here:
`docs/API_REFERENCE.md`

That file includes:
- Route registration mapping (base path -> router)
- All methods and paths grouped by feature area:
  - `/auth`, `/portal`, `/dashboard`, `/api/search`, `/api/report`
  - `/delivery-partners`
  - `/supermarkets/add` (multi-step wizard, now as API or converted flow)
  - `/supermarkets` (CRUD + subscription + exports)
  - `/analytics`
  - `/daily-activity`
  - `/api/v1/admin/invoices`
  - `/monitorapp`

### Frontend implications
Because the old backend also served UI pages, you have two approaches:
1. **Keep “page routes” as JSON endpoints**
   - Replace EJS pages with API calls returning data
2. **Keep some routes temporarily**
   - If you migrate gradually, you can run the old server-rendered pages in parallel during transition.

Recommended long-term approach:
- Convert UI routes like `GET /portal/invoices` into frontend routes, and have the frontend call `GET /portal/api/invoices`.

---

## File uploads and multipart endpoints
Current code uses `uploadTemp.single('photo')` for supermarket flows.
In the new backend:
- Keep upload endpoints as `multipart/form-data`
- Return JSON with the uploaded resource metadata, or redirect removal if using SPA.

If you prefer to remove multi-step forms from the URL structure:
- Still support the same final actions, but implement wizard state client-side.
- Backend can expose simple endpoints like:
  - `POST /supermarkets/add/step3` (photo upload)
  - `POST /supermarkets/add/summary` (final create)

---

## Suggested backend folder structure
Example structure for a fresh repo (or a cleaned decoupled branch):
```
src/
  app.ts
  server.ts
  config/
    env.ts
  api/
    routes/
      auth.routes.ts
      portal.routes.ts
      dashboard.routes.ts
      invoices.routes.ts
      ...
    controllers/
      auth.controller.ts
      invoices.controller.ts
      ...
    services/
      invoices.service.ts
      analytics.service.ts
      ...
    repositories/
      invoices.repo.ts
      supermarkets.repo.ts
      ...
    validators/
      auth.validator.ts
  middlewares/
    auth.middleware.ts
    apiKey.middleware.ts
    rateLimit.middleware.ts
    error.middleware.ts
  utils/
    exports/
      csv.ts
      pdf.ts
    errors/
      ApiError.ts
  tests/
    routes.int.test.ts
    controllers.unit.test.ts
```

If you keep JavaScript instead of TypeScript, use the same structure with `.js` files.

---

## Database and domain model (minimum set)
Based on feature area names in the current project, your backend likely needs these entities:
- `Supermarket` / `Shop`
- `Address` (if separate)
- `DeliveryPartner`
- `Subscription` (supermarket subscription)
- `Order` (and order status history)
- `Invoice`
- `InvoiceBill` (if separate)
- `InvoiceNote`
- `Customer` (and derived segments/behaviour)
- `AnalyticsCache` / `Metrics` (if persisted)

You can define schemas based on the existing PostgreSQL migrations in the repo (or reverse-engineer from the current services/models).

---

## Frontend integration contract
Frontend should provide:
1. **API client**
   - Central file: `src/lib/api.ts`
   - Auto-includes auth (cookies or headers)
2. **Route guards**
   - Blocks navigation if not authenticated
3. **Download helpers**
   - For CSV/PDF exports, call the endpoint and save blob
4. **Error handling**
   - Render validation errors from API responses

---

## Migration checklist (from current code to decoupled backend)
1. **Extract route handlers**
   - Move logic currently tied to EJS render into controller methods that return JSON
2. **Replace EJS pages with API responses**
   - Any route that previously rendered HTML should become a JSON endpoint (or be removed)
3. **Define new frontend routes**
   - `GET /portal/*` and `GET /dashboard/*` should become frontend pages (not backend pages)
4. **Harden auth**
   - Ensure OTP flows produce a secure session/JWT
5. **Add CORS and security headers**
   - `helmet`, cookie flags, CSRF if using cookies
6. **Add automated tests**
   - Integration tests for auth, invoices, exports
7. **Document the API**
   - Generate OpenAPI/Swagger (optional but recommended)
   - Ensure docs reference `docs/API_REFERENCE.md`

---

## Start-up requirements (what you should decide before coding)
1. Frontend framework: Next.js/React/etc.
2. Auth transport: sessions vs JWT.
3. Environment variables:
   - database URL
   - JWT/session secret
   - OTP provider (if any)
   - admin/metrics API keys
   - upload storage config
4. Export strategy: synchronous download endpoints or async jobs.

---

## Reference files in this repo
- `docs/API_REFERENCE.md` - all current routes (paths + methods)
- `src/routers/*.route.js` - source of truth for current Express route definitions

