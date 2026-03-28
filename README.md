# Yaadro Super Admin (India) — Backend

**FastAPI** service for shops, orders, delivery partners, subscriptions/invoices, reports, analytics, and OTP auth. Uses **SQLAlchemy** (PostgreSQL), **Pydantic**, **JWT**, and a layered **service → repository** design.

## Prerequisites

- **Python** 3.11+ (recommended)
- **PostgreSQL** reachable via your `DATABASE_URL` / settings
- Environment configured (see `app/api/core/config.py` and `settings`)

## Setup

```bash
cd backendIndianySuperadmin
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Configure database and secrets (e.g. `SECRET_KEY`, `DATABASE_URL`) through your environment or `.env` as expected by your deployment.

## Run (development)

From the `backendIndianySuperadmin` directory (where `app/` lives):

```bash
uvicorn app.main:app --app-dir . --reload --host 0.0.0.0 --port 8000
```

Health checks:

- `GET /health`
- `GET /health/ready`

## Tests

```bash
pytest tests/ -q
```

## Project layout (high level)

| Path | Role |
|------|------|
| `app/main.py` | FastAPI app factory, middleware, lifespan (DB readiness) |
| `app/api/` | Routers, deps, schemas, exception handlers |
| `app/services/` | Business logic, validation, transactions |
| `app/repositories/` | SQLAlchemy data access (no `commit()` in repos; services use `session_commit_scope`) |
| `app/domain/` | Domain exceptions, repository interfaces |
| `app/infrastructure/` | DB models, session, OTP, storage |
| `app/jobs/` | Scheduler-safe job entrypoints (explicit `Session`) |
| `tests/` | Unit and API tests |

## API documentation

- **OpenAPI**: `GET /docs` (Swagger UI) when the app is running.
- **Written guides** in this repo: `api.md`, `dashboard.md`, `application.md`, `models.md`, `fastapiarchitecture.md`.

## CORS / frontend

Point the Vite app at this server with `VITE_API_BASE_URL` (see frontend `README.md`). Default local dev assumes `http://127.0.0.1:8000`.

## License

Private — CodeTeak / Yaadro internal use unless stated otherwise.
