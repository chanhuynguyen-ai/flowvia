from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    workspace_default_timezone: str = "Asia/Ho_Chi_Minh"
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/flowvia"
    redis_url: str = "redis://localhost:6379/0"
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_bucket: str = "flowvia-local"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    session_cookie_secure: bool = False
    session_ttl_hours: int = 12
    seed_demo_data: bool = False
    outbound_mode: str = "dry_run"
    max_workflow_nodes: int = 50
    max_upload_bytes: int = 20 * 1024 * 1024
    credential_encryption_key: str = ""
    credential_key_file: str = ".data/credential.key"
    worker_poll_seconds: float = Field(default=0.5, ge=0.05, le=10)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_security_settings(self):
        if "*" in self.cors_origin_list:
            raise ValueError(
                "CORS_ORIGINS cannot contain '*' when credentialed web sessions are enabled"
            )
        if self.app_env.casefold() == "production" and not self.session_cookie_secure:
            raise ValueError("SESSION_COOKIE_SECURE must be true in production")
        if self.app_env.casefold() == "production" and (
            self.seed_demo_data or not self.credential_encryption_key
        ):
            raise ValueError(
                "Production requires an encryption key and SEED_DEMO_DATA=false"
            )
        if self.outbound_mode not in ("dry_run", "live"):
            raise ValueError("OUTBOUND_MODE must be dry_run or live")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
