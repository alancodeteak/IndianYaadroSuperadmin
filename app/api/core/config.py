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
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ISSUER: str = "yaadro-superadmin"
    JWT_AUDIENCE: str = "yaadro-superadmin-clients"

    REDIS_URL: str | None = None
    DEFAULT_PAGE_SIZE: int = 20
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
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

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

