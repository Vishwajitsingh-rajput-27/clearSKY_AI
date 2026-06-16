from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UserSignupRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=160)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return validate_email(value)


class UserLoginRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return validate_email(value)


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    is_verified: bool
    storage_quota_bytes: int
    used_storage_bytes: int
    created_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserResponse


class StorageUsageResponse(BaseModel):
    storage_quota_bytes: int
    used_storage_bytes: int
    remaining_storage_bytes: int
    usage_percent: float


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    status: str
    storage_used_bytes: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserHistoryItem(BaseModel):
    id: UUID
    kind: str
    title: str
    status: str
    project_id: UUID | None = None
    model: str | None = None
    quality_score: float | None = None
    storage_bytes: int = 0
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserHistoryResponse(BaseModel):
    items: list[UserHistoryItem]
    storage: StorageUsageResponse


def validate_email(value: str) -> str:
    normalized = value.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ValueError("Enter a valid email address.")

    local, _, domain = normalized.partition("@")
    if not local or "." not in domain:
        raise ValueError("Enter a valid email address.")

    return normalized
