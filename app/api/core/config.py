from functools import lru_cache
import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _env_name = os.getenv("ENVIRONMENT", "dev")
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{_env_name}"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Yadro Superadmin API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite+pysqlite:///./superadmin.db"
    # PostgreSQL connection pool (ignored for SQLite URL schemes)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE_SECONDS: int = 1800
    # When True, startup fails if DB ping fails (recommended for production).
    FAIL_FAST_ON_DB_ERROR: bool = False
    # Compress large JSON/text responses (Starlette GZip middleware).
    ENABLE_RESPONSE_GZIP: bool = True
    GZIP_MINIMUM_SIZE: int = 1000
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ISSUER: str = "yaadro-superadmin"
    JWT_AUDIENCE: str = "yaadro-superadmin-clients"
    OTP_TTL_SECONDS: int = 300
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_MAX_ATTEMPTS: int = 5
    OTP_LOG_TO_TERMINAL: bool = False
    ADMIN_OTP_EMAILS: str = ""
    PORTAL_OTP_EMAILS: str = ""
    # Single-portal-user convenience: when set, only this email may use portal OTP flow.
    # Still requires DB mapping to a shop (validated at startup).
    PORTAL_DEFAULT_EMAIL: str = ""
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Yadro Superadmin"

    REDIS_URL: str | None = None
    DEFAULT_PAGE_SIZE: int = 20
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,testserver"
    FORCE_HTTPS_REDIRECT: bool = False

    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    ADMIN_API_KEY: str = ""
    METRICS_API_KEY: str = ""

    ENABLE_ADMIN_API_KEY_PROTECTION: bool = True
    ENABLE_METRICS_API_KEY_PROTECTION: bool = True
    ENABLE_DETAILED_HEALTH: bool = False

    # AWS / S3 (uploads & image access)
    AWS_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_ACCOUNT_ID: str = ""
    AWS_S3_KMS_KEY_ID: str = ""
    S3_PRESIGNED_URL_EXPIRY: int = 3600
    S3_MAX_FILE_SIZE: int = 10_485_760
    PROD_S3_BUCKET_DELIVERY_PARTNER: str = ""
    PROD_S3_BUCKET_ORDERS: str = ""
    PROD_S3_BUCKET_TICKETS: str = ""
    PROD_S3_BUCKET_SHOP_OWNER: str = ""

    TZ: str = "UTC"

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.ENVIRONMENT.lower() in {"production", "prod"}:
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            if self.SECRET_KEY.lower() in {"change-me", "changeme", "secret", "default"}:
                raise ValueError("SECRET_KEY is weak/default; use a strong random value")

            if self.CORS_ORIGINS.strip() in {"*", ""}:
                raise ValueError("CORS_ORIGINS must be an explicit allowlist in production")
            if not self.FORCE_HTTPS_REDIRECT:
                raise ValueError("FORCE_HTTPS_REDIRECT must be true in production")

        if self.ENABLE_ADMIN_API_KEY_PROTECTION and not self.ADMIN_API_KEY:
            raise ValueError(
                "ADMIN_API_KEY is required when ENABLE_ADMIN_API_KEY_PROTECTION is true"
            )
        if self.ENABLE_METRICS_API_KEY_PROTECTION and not self.METRICS_API_KEY:
            raise ValueError(
                "METRICS_API_KEY is required when ENABLE_METRICS_API_KEY_PROTECTION is true"
            )
        if self.OTP_TTL_SECONDS <= 0:
            raise ValueError("OTP_TTL_SECONDS must be > 0")
        if self.OTP_RESEND_COOLDOWN_SECONDS < 0:
            raise ValueError("OTP_RESEND_COOLDOWN_SECONDS must be >= 0")
        if self.OTP_MAX_ATTEMPTS < 1:
            raise ValueError("OTP_MAX_ATTEMPTS must be >= 1")
        if self.SMTP_USE_TLS and self.SMTP_USE_SSL:
            raise ValueError("SMTP_USE_TLS and SMTP_USE_SSL cannot both be true")
        if self.SMTP_ENABLED:
            if not self.SMTP_HOST:
                raise ValueError("SMTP_HOST is required when SMTP_ENABLED is true")
            if not self.SMTP_PORT:
                raise ValueError("SMTP_PORT is required when SMTP_ENABLED is true")
            if not self.SMTP_FROM_EMAIL:
                raise ValueError("SMTP_FROM_EMAIL is required when SMTP_ENABLED is true")
            if not self.SMTP_USERNAME:
                raise ValueError("SMTP_USERNAME is required when SMTP_ENABLED is true")
            if not self.SMTP_PASSWORD:
                raise ValueError("SMTP_PASSWORD is required when SMTP_ENABLED is true")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

