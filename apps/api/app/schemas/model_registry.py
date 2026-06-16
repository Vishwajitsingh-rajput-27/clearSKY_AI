from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ModelRegistryResponse(BaseModel):
    id: UUID
    model_name: str
    version: str
    architecture: str
    runtime_type: str
    input_modalities: dict[str, Any] | None = None
    dataset_version: str | None = None
    training_date: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    checkpoint_path: str | None = None
    checkpoint_status: str = "missing"
    stage: str = "research"
    is_active: bool = True
    is_best: bool = False
    created_at: datetime | None = None


class ExperimentRunResponse(BaseModel):
    id: UUID
    model_id: UUID | None = None
    experiment_name: str
    model_name: str
    version: str
    status: str
    training_date: datetime | None = None
    dataset_version: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    checkpoint_path: str | None = None
    checkpoint_score: float | None = None
    is_best: bool = False
    notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None


class ModelCheckpointResponse(BaseModel):
    id: UUID
    model_id: UUID | None = None
    experiment_id: UUID | None = None
    model_name: str
    version: str
    checkpoint_path: str
    storage_uri: str | None = None
    status: str
    epoch: int | None = None
    metric_name: str | None = None
    metric_value: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    file_size_bytes: int | None = None
    is_best: bool = False
    created_at: datetime | None = None


class ExperimentMetricResponse(BaseModel):
    id: UUID
    experiment_id: UUID | None = None
    model_name: str
    version: str
    split: str
    epoch: int | None = None
    step: int | None = None
    loss: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime | None = None
    created_at: datetime | None = None


class ModelRegistrySummaryResponse(BaseModel):
    registered_models: int
    active_models: int
    experiment_count: int
    checkpoint_count: int
    best_model: ModelRegistryResponse | None = None
    latest_training_date: datetime | None = None
    best_quality_score: float | None = None
