import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id"), index=True)
    metric_set: Mapped[str] = mapped_column(String(64), default="foundation")
    psnr: Mapped[float | None] = mapped_column(Float)
    ssim: Mapped[float | None] = mapped_column(Float)
    sam: Mapped[float | None] = mapped_column(Float)
    ergas: Mapped[float | None] = mapped_column(Float)
    rmse: Mapped[float | None] = mapped_column(Float)
    ndvi_delta: Mapped[float | None] = mapped_column(Float)
    cloud_iou: Mapped[float | None] = mapped_column(Float)
    shadow_iou: Mapped[float | None] = mapped_column(Float)
    runtime_seconds: Mapped[float | None] = mapped_column(Float)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
