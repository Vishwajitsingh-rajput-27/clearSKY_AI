import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id"),
        index=True,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id"))
    scene_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("scenes.id"))
    inference_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("inference_runs.id"),
    )
    asset_type: Mapped[str] = mapped_column(String(64), index=True)
    storage_url: Mapped[str] = mapped_column(String(2048))
    local_path: Mapped[str | None] = mapped_column(String(2048))
    storage_provider: Mapped[str | None] = mapped_column(String(32), default="local")
    external_id: Mapped[str | None] = mapped_column(String(1024))
    filename: Mapped[str | None] = mapped_column(String(512))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    checksum: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
