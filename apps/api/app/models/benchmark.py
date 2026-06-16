import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inference_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("inference_runs.id"),
        index=True,
    )
    metric_mode: Mapped[str] = mapped_column(String(32), default="no_reference_proxy", index=True)
    requested_model: Mapped[str] = mapped_column(String(128))
    used_model: Mapped[str] = mapped_column(String(128))
    psnr: Mapped[float | None] = mapped_column(Float)
    ssim: Mapped[float | None] = mapped_column(Float)
    rmse: Mapped[float | None] = mapped_column(Float)
    mae: Mapped[float | None] = mapped_column(Float)
    sam: Mapped[float | None] = mapped_column(Float)
    spectral_consistency_score: Mapped[float | None] = mapped_column(Float)
    cloud_reduction_score: Mapped[float | None] = mapped_column(Float)
    no_reference_quality_score: Mapped[float | None] = mapped_column(Float)
    processing_time_seconds: Mapped[float | None] = mapped_column(Float)
    report_json_url: Mapped[str | None] = mapped_column(String(2048))
    report_markdown_url: Mapped[str | None] = mapped_column(String(2048))
    metrics: Mapped[dict | None] = mapped_column(JSON)
    benchmark_rows: Mapped[list | None] = mapped_column(JSON)
    explanation: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
