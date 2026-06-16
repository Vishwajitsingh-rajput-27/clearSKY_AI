from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SceneCreateRequest(BaseModel):
    filename: str
    client_scene_id: UUID = Field(default_factory=uuid4)
    sensor: str = "LISS-IV"
    project_id: UUID | None = None


class SceneResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    project_id: UUID | None = None
    filename: str
    original_filename: str | None = None
    safe_filename: str | None = None
    sensor: str
    status: str
    content_type: str | None = None
    file_size_bytes: int | None = None
    checksum_sha256: str | None = None
    storage_url: str | None = None
    storage_provider: str | None = None
    external_id: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
