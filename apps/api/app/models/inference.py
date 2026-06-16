import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InferenceRun(Base):
    __tablename__ = "inference_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    requested_model: Mapped[str] = mapped_column(String(128))
    used_model: Mapped[str] = mapped_column(String(128))
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=True)
    original_image_url: Mapped[str] = mapped_column(String(2048))
    cloud_mask_url: Mapped[str] = mapped_column(String(2048))
    shadow_mask_url: Mapped[str] = mapped_column(String(2048))
    reconstructed_image_url: Mapped[str] = mapped_column(String(2048))
    difference_map_url: Mapped[str] = mapped_column(String(2048))
    attention_map_url: Mapped[str | None] = mapped_column(String(2048))
    confidence_map_url: Mapped[str | None] = mapped_column(String(2048))
    analysis_geotiff_url: Mapped[str | None] = mapped_column(String(2048))
    qgis_manifest_url: Mapped[str | None] = mapped_column(String(2048))
    cloud_coverage_percent: Mapped[float] = mapped_column(Float)
    shadow_coverage_percent: Mapped[float] = mapped_column(Float)
    quality_score: Mapped[float] = mapped_column(Float)
    reconstruction_confidence_score: Mapped[float | None] = mapped_column(Float)
    processing_time_seconds: Mapped[float] = mapped_column(Float)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    recommendations: Mapped[list | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
