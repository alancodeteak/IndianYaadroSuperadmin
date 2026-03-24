from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.core.config import Settings


def apply_cors(app: FastAPI, settings: Settings) -> None:
    origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    if not origins:
        origins = ["http://localhost:3000"]

    wildcard = "*" in origins
    allow_credentials = not wildcard

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-API-KEY",
            "X-Request-ID",
            "X-Requested-With",
            "Accept",
            "Origin",
        ],
    )

