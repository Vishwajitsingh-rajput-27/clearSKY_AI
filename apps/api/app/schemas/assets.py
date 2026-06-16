from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssetRead(BaseModel):
    id: UUID
    job_id: UUID | None = None
    scene_id: UUID | None = None
    asset_type: str
    storage_url: str
    storage_provider: str | None = None
    external_id: str | None = None
    filename: str | None = None
    file_size_bytes: int | None = None
    mime_type: str | None = None
    checksum: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
