from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "clearSKY AI API"
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    api_prefix: str = "/api"
    frontend_url: str | None = None
    backend_url: str | None = None
    allowed_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "CORS_ORIGINS"),
    )
    database_url: str | None = None
    sqlite_database_path: Path = Path(".local/clearsky.db")
    auto_create_tables: bool = True
    upload_dir: Path = Path(".local/uploads")
    served_files_enabled: bool = True
    allowed_upload_extensions: Annotated[list[str], NoDecode] = [".tif", ".tiff", ".zip"]
    allowed_inference_extensions: Annotated[list[str], NoDecode] = [
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".jp2",
        ".j2k",
    ]
    inference_dir: Path = Path(".local/inference")
    max_inference_dimension: int = 2048
    max_inference_pixels: int = 25_000_000
    storage_provider: Literal["local", "cloudinary", "supabase"] = "local"
    cloudinary_url: str = ""
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "clearsky"
    api_internal_token: str = "change-me"
    jwt_secret: str = Field(default="dev-only-change-me", validation_alias="JWT_SECRET")
    access_token_expire_minutes: int = 60 * 24
    default_user_storage_quota_mb: int = 512
    model_dir: Path = Path("./models")
    max_upload_size_mb: int = Field(
        default=512,
        validation_alias=AliasChoices("MAX_UPLOAD_SIZE_MB", "MAX_UPLOAD_MB"),
    )
    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("allowed_upload_extensions", mode="before")
    @classmethod
    def parse_upload_extensions(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            value = [extension.strip() for extension in value.split(",") if extension.strip()]

        return [
            extension.lower() if extension.startswith(".") else f".{extension.lower()}"
            for extension in value
        ]

    @field_validator("allowed_inference_extensions", mode="before")
    @classmethod
    def parse_inference_extensions(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            value = [extension.strip() for extension in value.split(",") if extension.strip()]

        return [
            extension.lower() if extension.startswith(".") else f".{extension.lower()}"
            for extension in value
        ]

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        production = self.app_env.lower() == "production"

        if production and not self.database_url:
            raise ValueError("DATABASE_URL is required when APP_ENV=production")

        if production and self.storage_provider == "local":
            raise ValueError("STORAGE_PROVIDER must be cloudinary or supabase in production")

        if production and self.jwt_secret == "dev-only-change-me":
            raise ValueError("JWT_SECRET must be set to a strong secret in production")

        if self.storage_provider == "cloudinary" and not self.cloudinary_configured:
            raise ValueError("CLOUDINARY_URL or CLOUDINARY_* credentials are required")

        if self.storage_provider == "supabase" and not self.supabase_configured:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

        return self

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.rstrip("/") for origin in self.allowed_origins]

        if self.frontend_url:
            origins.append(self.frontend_url.rstrip("/"))

        return sorted(set(origin for origin in origins if origin))

    @computed_field
    @property
    def resolved_database_url(self) -> str:
        if not self.database_url:
            sqlite_path = self.sqlite_database_path
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{sqlite_path.as_posix()}"

        return normalize_database_url(self.database_url)

    @computed_field
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @computed_field
    @property
    def default_user_storage_quota_bytes(self) -> int:
        return self.default_user_storage_quota_mb * 1024 * 1024

    @computed_field
    @property
    def is_sqlite(self) -> bool:
        return self.resolved_database_url.startswith("sqlite")

    @computed_field
    @property
    def cloudinary_configured(self) -> bool:
        return bool(
            self.cloudinary_url
            or (
                self.cloudinary_cloud_name
                and self.cloudinary_api_key
                and self.cloudinary_api_secret
            )
        )

    @computed_field
    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    @computed_field
    @property
    def public_backend_url(self) -> str | None:
        return self.backend_url.rstrip("/") if self.backend_url else None

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)

    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
