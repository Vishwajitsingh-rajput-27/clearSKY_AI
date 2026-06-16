import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ModelRegistry(Base):
    __tablename__ = "models"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64))
    architecture: Mapped[str] = mapped_column(String(128))
    runtime_type: Mapped[str] = mapped_column(String(64), default="pytorch")
    input_modalities: Mapped[dict | None] = mapped_column(JSON)
    dataset_version: Mapped[str | None] = mapped_column(String(128), index=True)
    training_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    checkpoint_path: Mapped[str | None] = mapped_column(String(2048))
    checkpoint_status: Mapped[str | None] = mapped_column(String(64), default="missing")
    stage: Mapped[str | None] = mapped_column(String(64), default="research")
    is_best: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id"), index=True)
    model_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("models.id"))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    runtime_seconds: Mapped[float | None] = mapped_column(Float)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("models.id"),
        index=True,
    )
    experiment_name: Mapped[str] = mapped_column(String(160), index=True)
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="planned", index=True)
    training_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    dataset_version: Mapped[str | None] = mapped_column(String(128), index=True)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    hyperparameters: Mapped[dict | None] = mapped_column(JSON)
    checkpoint_path: Mapped[str | None] = mapped_column(String(2048))
    checkpoint_score: Mapped[float | None] = mapped_column(Float)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelCheckpoint(Base):
    __tablename__ = "model_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("models.id"),
        index=True,
    )
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiment_runs.id"),
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    checkpoint_path: Mapped[str] = mapped_column(String(2048))
    storage_uri: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(32), default="missing", index=True)
    epoch: Mapped[int | None] = mapped_column(Integer)
    metric_name: Mapped[str | None] = mapped_column(String(64))
    metric_value: Mapped[float | None] = mapped_column(Float)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExperimentMetric(Base):
    __tablename__ = "experiment_metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiment_runs.id"),
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    split: Mapped[str] = mapped_column(String(32), default="validation", index=True)
    epoch: Mapped[int | None] = mapped_column(Integer)
    step: Mapped[int | None] = mapped_column(Integer)
    loss: Mapped[float | None] = mapped_column(Float)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
