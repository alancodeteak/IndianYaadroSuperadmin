# FastAPI Clean Architecture - Backend File Architecture

This document proposes a “Clean Architecture” file/folder structure for a **FastAPI API-only backend** (no EJS), while keeping the same route groups you already have:
`/auth`, `/portal`, `/dashboard`, `/api/search`, `/api/report`, `/delivery-partners`, `/supermarkets/*`, `/analytics`, `/daily-activity`, `/api/v1/admin/invoices`, `/monitorapp`.

It is designed so:
- FastAPI routers are thin (presentation layer)
- business rules live in the application/domain layers
- database/email/storage/export implementations live in infrastructure
- you can test use cases without the web framework

Clean Architecture rule used in this document:
- dependency direction always points inward:
  - `api` -> `application` -> `domain`
  - `infrastructure` -> `domain` (and optionally `application` for wiring only)
- `domain` and `application` must not import FastAPI, SQLAlchemy, Redis, SMTP clients, or other framework/vendor packages

---

## 1. High-level layer responsibilities

**API (presentation)**
- FastAPI app wiring: routers, middleware, exception handlers
- Request parsing + response formatting
- Authentication dependencies (translate token/cookie to a `CurrentUser` object)

**Application (use cases)**
- Orchestrates business flows (OTP verify, invoice generation, exports, etc.)
- Validates business invariants using domain rules
- Defines input/output contracts (DTOs) for use cases
- Declares service/repository ports required by use cases

**Domain (enterprise rules)**
- Entities/value objects
- Domain services (if needed)
- Repository interfaces (ports) used by use cases
- Domain exceptions
- Pure business logic only (no HTTP, ORM, framework types)

**Infrastructure (adapters)**
- Database access (SQLAlchemy + Alembic)
- Repositories implementing domain interfaces
- External systems (email, PDF generation, cache, rate limiting, object storage)
- Implementations for service ports declared by application/domain

---

## 2. Suggested repository layout (clean-architecture compliant)

Use this structure as a new backend repo (or as a major refactor branch).

```
superadmin-backend/
  app/
    __init__.py
    main.py
    api/
      __init__.py
      deps.py
      router.py
      middlewares/
        __init__.py
        request_id.py
        auth.py
        api_key.py
        rate_limit.py
      exceptions/
        __init__.py
        handlers.py
        http_errors.py
      v1/
        __init__.py
        routers/
          __init__.py
          auth.py
          portal.py
          dashboard.py
          search.py
          report.py
          delivery_partners.py
          supermarkets_add.py
          supermarkets.py
          analytics.py
          daily_activity.py
          invoices.py
          monitorapp.py
        schemas/
          __init__.py
          common.py
          auth.py
          portal.py
          dashboard.py
          search.py
          report.py
          delivery_partners.py
          supermarkets.py
          analytics.py
          daily_activity.py
          invoices.py
          monitorapp.py
    application/
      __init__.py
      use_cases/
        __init__.py
        auth/
          __init__.py
          send_otp.py
          verify_otp.py
          login_session.py
          logout.py
        portal/
          __init__.py
          send_portal_otp.py
          verify_portal_otp.py
          portal_logout.py
        dashboard/
          __init__.py
          get_dashboard.py
          get_system_monitoring.py
          get_inventory_management.py
          get_shop_customers.py
          get_filtered_orders.py
          get_all_shops.py
          get_export_orders.py
          get_shop_owners.py
          get_delivery_partners.py
          get_recent_activities.py
          rebuild_cache.py
          get_socket_stats.py
          get_detailed_socket_metrics.py
          get_cache_stats.py
          update_payment_status.py
          update_payment_status_form.py
          trigger_maintenance.py
          get_maintenance_cooldown.py
        search/
          __init__.py
          search_all.py
        report/
          __init__.py
          generate_report.py
        delivery_partners/
          __init__.py
          list_delivery_partners.py
          list_delivery_partners_by_shop.py
          get_delivery_partner_details.py
          block_delivery_partner.py
          update_delivery_partner.py
          delete_delivery_partner.py
          restore_delivery_partner.py
        supermarkets_add/
          __init__.py
          step1_handle.py
          step2_handle.py
          step3_handle_upload.py
          step4_handle.py
          render_summary.py
          submit_summary.py
          block_supermarket.py
          unblock_supermarket.py
        supermarkets/
          __init__.py
          list_supermarkets.py
          get_supermarket_details.py
          get_supermarket_pdf.py
          render_edit.py
          update_supermarket.py
          get_supermarket_orders.py
          get_order_statistics.py
          create_subscription.py
          update_subscription_amount.py
          download_supermarkets_report.py
          soft_delete_supermarket.py
          restore_supermarket.py
          list_deleted_supermarkets.py
          check_shop_id.py
          check_user_id.py
        analytics/
          __init__.py
          get_analytics.py
          get_supermarket_analytics.py
          get_market_study_analytics.py
          update_analytics_filter.py
          get_analytics_cache.py
          set_analytics_cache.py
          get_rate_limit_info.py
          increment_rate_limit.py
          download_chart_pdf.py
        daily_activity/
          __init__.py
          get_daily_activity_page_data.py
          export_daily_activity_csv.py
        invoices/
          __init__.py
          list_invoices.py
          list_shops_with_subscriptions.py
          get_monthly_summary.py
          create_manual_invoice.py
          create_manual_bill.py
          create_fully_manual_invoice.py
          download_invoice.py
          get_invoice.py
          update_invoice_status.py
          update_invoice.py
          patch_invoice.py
          retry_bill_generation.py
          generate_bills_for_paid.py
          generate_monthly_invoices.py
          generate_monthly_for_month.py
          run_status_automation.py
          issue_invoice.py
          generate_invoice_for_subscription.py
          create_dummy_invoice_data.py
          send_invoice_email.py
          send_followup_email.py
          get_notes.py
          add_note.py
          delete_note.py
          sync_notes.py
        monitorapp/
          __init__.py
          monitorapp_verify_password.py
          monitorapp_show_dashboard.py
          monitorapp_verify_shop_password.py
          monitorapp_lock_shop_data.py
          monitorapp_download_shop_app.py
          monitorapp_download_shop_app_x64.py
          monitorapp_download_shop_app_x86.py
          monitorapp_logout.py
    domain/
      __init__.py
      entities/
        __init__.py
        supermarket.py
        delivery_partner.py
        subscription.py
        order.py
        invoice.py
        invoice_note.py
        analytics_models.py
        customer.py
      value_objects/
        __init__.py
        ids.py
        money.py
      enums/
        __init__.py
        roles.py
        invoice_status.py
      exceptions/
        __init__.py
        domain_errors.py
      repositories/
        __init__.py
        auth_repositories.py
        portal_repositories.py
        dashboard_repositories.py
        delivery_partner_repositories.py
        supermarket_repositories.py
        analytics_repositories.py
        invoice_repositories.py
        monitorapp_repositories.py
        export_repositories.py
      services/
        __init__.py
        otp_service.py
        invoice_service.py
        export_service.py
    infrastructure/
      __init__.py
      db/
        __init__.py
        session.py
        models/
          __init__.py
          supermarket.py
          delivery_partner.py
          subscription.py
          order.py
          invoice.py
          invoice_note.py
          analytics_models.py
          customer.py
        repositories/
          __init__.py
          auth_repo.py
          portal_repo.py
          dashboard_repo.py
          delivery_partner_repo.py
          supermarket_repo.py
          analytics_repo.py
          invoice_repo.py
          monitorapp_repo.py
        migrations/
          env.py
          versions/
            # alembic autogenerated
      security/
        __init__.py
        otp_service_impl.py
        jwt_service_impl.py
        session_service_impl.py
        api_key_service_impl.py
      integrations/
        __init__.py
        email_service.py
        pdf_renderer.py
        chart_renderer.py
      storage/
        __init__.py
        upload_storage.py
        filesystem_storage.py
        s3_storage.py
      exports/
        __init__.py
        csv_exporter.py
        pdf_exporter.py
        excel_exporter.py
      cache/
        __init__.py
        redis_cache.py
      rate_limit/
        __init__.py
        limiter_impl.py
      utils/
        __init__.py
        file_streams.py
    shared/
      __init__.py
      config.py
      logging.py
      http/
        __init__.py
        status_codes.py
      schemas/
        __init__.py
        pagination.py
      time.py
  tests/
    __init__.py
    unit/
      test_otp_service.py
      test_invoice_service.py
    integration/
      api/
        test_auth.py
        test_invoices.py
        test_exports.py
      db/
        test_repositories.py
    e2e/
      test_smoke.py
  scripts/
    run_dev.py
    generate_openapi.py
  alembic.ini
  Dockerfile
  README.md
  requirements.txt
```

---

## 3. “All routers + schemas” mapping (what goes where)

Your new FastAPI backend should expose one router per feature area. Each router should:
1. Define the endpoints (matching the existing API contract in `docs/API_REFERENCE.md`)
2. Use a dependency for auth (`CurrentUser` / roles)
3. Call exactly one application use case per endpoint

Important:
- router and schema modules are transport concerns only
- do not pass ORM models outside infrastructure
- convert request models -> use-case input DTOs, and use-case output DTOs -> response models

### Routers
- `app/api/v1/routers/auth.py` -> `GET/POST /auth/login`, `/auth/logout`, `/auth/send-otp`, `/auth/verify-otp`
- `app/api/v1/routers/portal.py` -> `GET/POST /portal/*` + portal API endpoints
- `app/api/v1/routers/dashboard.py` -> all `/dashboard/*` endpoints that are data/actions
- `app/api/v1/routers/search.py` -> `GET /api/search/`
- `app/api/v1/routers/report.py` -> `POST /api/report/`
- `app/api/v1/routers/delivery_partners.py` -> `/delivery-partners/*`
- `app/api/v1/routers/supermarkets_add.py` -> `/supermarkets/add/*` wizard actions
- `app/api/v1/routers/supermarkets.py` -> `/supermarkets/*` CRUD/actions
- `app/api/v1/routers/analytics.py` -> `/analytics/*`
- `app/api/v1/routers/daily_activity.py` -> `/daily-activity/*`
- `app/api/v1/routers/invoices.py` -> `/api/v1/admin/invoices/*`
- `app/api/v1/routers/monitorapp.py` -> `/monitorapp/*`

### Schemas
- Keep API request/response models in `app/api/v1/schemas/*.py`
- Keep shared pagination/error contracts in `common.py`

---

## 4. Dependency injection pattern (how routers call use cases)

Suggested pattern:
1. `app/api/deps.py` creates dependencies:
   - DB session
   - repository implementations (infrastructure)
   - use case construction (application)
2. `app/api/v1/routers/*.py` imports and uses deps.

Typical dependency responsibilities:
- `get_db_session()`
- `get_current_user()` (maps JWT/session -> domain role)
- `get_delivery_partner_repository()`
- etc.

This avoids importing SQLAlchemy models directly in routers or use cases.

Composition-root rule:
- keep DI assembly at app startup / dependency modules (`app/main.py`, `app/api/deps.py`)
- construct concrete infrastructure adapters there
- inject only interfaces/ports into use cases

---

## 5. Error handling architecture (implement this first)

Build error handling as a first-class cross-cutting module, not per-router logic.
The goal is deterministic, debuggable, and layer-safe errors.

### 5.1 Canonical API error response

All API failures return this envelope:
- `{"error": {"code": "INV_NOT_FOUND", "message": "...", "details": {...}, "request_id": "..."}}`

Rules:
- `code` is stable and machine-readable (used by frontend/monitoring)
- `message` is client-safe (no stack traces, no SQL/internal details)
- `details` is optional structured context for validation/business errors
- `request_id` always present (set by request-id middleware)

### 5.2 File-level architecture (who owns what)

Use these files and responsibilities:

- `app/domain/exceptions/domain_errors.py`
  - base domain error + business-specific errors
  - no HTTP status codes, no FastAPI imports

- `app/application/exceptions/application_errors.py`
  - orchestration/use-case errors (authorization at use-case boundary, conflict states, idempotency failures)
  - no framework imports

- `app/infrastructure/exceptions/infrastructure_errors.py`
  - adapter failures (db unavailable, provider timeout, storage unavailable, email failure)
  - wraps vendor exceptions into internal infrastructure errors

- `app/api/exceptions/http_errors.py`
  - API-facing transport exceptions (if needed for explicit HTTP raises in presentation only)

- `app/api/exceptions/error_codes.py`
  - centralized error-code constants (single source of truth)

- `app/api/exceptions/schemas.py`
  - Pydantic error envelope schema used by OpenAPI and handlers

- `app/api/exceptions/mappers.py`
  - maps domain/application/infrastructure exceptions to `(status_code, error_code, safe_message)`

- `app/api/exceptions/handlers.py`
  - FastAPI exception handlers wiring for:
    - domain/application/infrastructure base exceptions
    - `RequestValidationError`
    - `HTTPException`
    - uncaught `Exception`

- `app/api/middlewares/request_id.py`
  - injects `request_id` into request state/contextvar + response headers

- `app/shared/logging.py`
  - structured logger helpers, ensuring errors include `request_id`, `error_code`, and exception class

### 5.3 Dependency direction constraints for errors

- `domain` errors can be raised by domain + application
- `application` errors can be raised by application
- `infrastructure` errors are raised only by infrastructure adapters
- `api` layer is the only place that converts internal errors to HTTP responses
- never raise `HTTPException` from domain/application/infrastructure

### 5.4 Error taxonomy (recommended)

Create base classes and category classes:

- Domain:
  - `DomainError`
  - `EntityNotFoundError`
  - `BusinessRuleViolationError`
  - `DomainConflictError`

- Application:
  - `ApplicationError`
  - `UseCaseValidationError`
  - `AuthorizationError`
  - `IdempotencyError`

- Infrastructure:
  - `InfrastructureError`
  - `DatabaseUnavailableError`
  - `ExternalServiceTimeoutError`
  - `StorageError`

Each concrete error should carry:
- `code` (stable internal code; mapped to API code in mapper if needed)
- `message` (internal message)
- `details: dict | None`

### 5.5 HTTP mapping matrix

Enforce one mapping table in `app/api/exceptions/mappers.py`:

- `EntityNotFoundError` -> `404`
- `BusinessRuleViolationError` -> `422`
- `DomainConflictError` -> `409`
- `UseCaseValidationError` -> `422`
- `AuthorizationError` -> `403` (or `401` if unauthenticated)
- `DatabaseUnavailableError` -> `503`
- `ExternalServiceTimeoutError` -> `504`
- unknown/unexpected exception -> `500` with generic code like `INTERNAL_SERVER_ERROR`

Validation:
- `RequestValidationError` -> `422`, code `REQUEST_VALIDATION_ERROR`, include field-level details

### 5.6 Logging and observability rules

- Log every handled error once in exception handlers (avoid duplicate logs in routers)
- Include:
  - `request_id`
  - `path`, `method`
  - `status_code`
  - `error_code`
  - exception class name
- For 5xx errors, log stack trace; for 4xx errors, no stack trace by default
- Add metric counters by `status_code` and `error_code` (if metrics middleware exists)

### 5.7 Router and use-case behavior rules

- Routers:
  - do not use broad `try/except Exception`
  - only parse request, call use case, map response

- Use cases:
  - raise domain/application exceptions only
  - never return partial success with hidden errors

- Repositories/adapters:
  - catch vendor exceptions (`SQLAlchemyError`, client timeouts, etc.)
  - wrap and raise infrastructure exceptions

### 5.8 Startup wiring checklist

In `app/main.py`:
1. register request-id middleware first
2. register other middlewares
3. register exception handlers via a single function (e.g., `register_exception_handlers(app)`)
4. include routers

In `app/api/exceptions/handlers.py`:
- keep one registration function; no scattered handler registration

### 5.9 Test architecture for error handling

Implement tests in this order:

1. Unit tests:
   - `tests/domain/test_domain_errors.py` (error object contracts)
   - `tests/api/test_error_mappers.py` (exception -> status/code mapping)

2. Integration tests:
   - `tests/api/test_error_handlers.py`
   - verify envelope format, request_id presence, and status codes

3. Regression tests:
   - one test per critical business error code (invoices, auth, supermarkets, delivery partners)

Minimum assertions per API error response:
- has `error.code`
- has `error.message`
- has `error.request_id`
- does not expose internal stack/sql/vendor payload

### 5.10 Practical first implementation sequence

1. create base exception classes in domain/application/infrastructure
2. add API error schema + error-code constants
3. implement mapper + global handlers
4. wire request-id middleware + handler registration in `app/main.py`
5. migrate one feature (recommended: `invoices`) to use new errors
6. add tests before moving to other feature modules

---

## 6. Exports (CSV/PDF/Excel) pattern

Because exports are part of “actions”, handle them in:
- Use cases in `app/application/use_cases/*/` (export use cases)
- Export implementations in:
  - `app/infrastructure/exports/*`

Return types:
- `StreamingResponse` for large files (preferred)
- correct `Content-Disposition` and `Content-Type`

---

## 7. Clean architecture guardrails (must follow)

Use these as acceptance criteria for every new module:

1. `domain` imports nothing from `api`, `application`, `infrastructure`, `shared` framework wrappers, or vendor SDKs
2. `application` imports from `domain` only (plus stdlib/typing)
3. `api` never touches ORM models directly and never contains business rules
4. `infrastructure` can depend on inner layers, never the other way around
5. long-running/background jobs call application use cases (not repositories directly)
6. all cross-layer communication uses explicit DTOs or value objects

Common anti-patterns to reject in review:
- use case returns `Response`, `StreamingResponse`, or framework-specific types
- repository interfaces declared in infrastructure instead of domain/application
- business logic inside router functions
- domain entities importing `pydantic`, `sqlalchemy`, or FastAPI classes

---

## 8. What you must implement first (practical order)
1. App skeleton: `app/main.py`, `api/router.py`, auth dependency, exception handlers
2. DB session + Alembic migrations
3. One feature end-to-end:
   - `delivery-partners` or `invoices`
4. Add remaining routers/use cases incrementally using the API reference file

---

## 9. Reference
- API contract: `docs/API_REFERENCE.md`
- Blueprint: `docs/DECOUPLED_BACKEND_FRONTEND_BLUEPRINT.md`

