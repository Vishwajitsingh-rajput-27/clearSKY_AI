from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class JobCreateRequest(BaseModel):
    scene_id: UUID
    client_job_id: UUID = Field(default_factory=uuid4)
    project_id: UUID | None = None
    selected_mode: str = "scientific"
    selected_model: str = "foundation"


class JobResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    project_id: UUID | None = None
    scene_id: UUID | None
    status: str
    selected_mode: str
    selected_model: str
    progress: int
    error_message: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
