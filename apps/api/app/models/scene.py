import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id"),
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(512))
    original_filename: Mapped[str | None] = mapped_column(String(512))
    safe_filename: Mapped[str | None] = mapped_column(String(512), index=True)
    sensor: Mapped[str] = mapped_column(String(64), default="LISS-IV")
    status: Mapped[str] = mapped_column(String(32), default="registered", index=True)
    content_type: Mapped[str | None] = mapped_column(String(128))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    local_path: Mapped[str | None] = mapped_column(String(2048))
    storage_provider: Mapped[str | None] = mapped_column(String(32), default="local")
    external_id: Mapped[str | None] = mapped_column(String(1024))
    band_count: Mapped[int | None] = mapped_column(Integer)
    crs: Mapped[str | None] = mapped_column(String(128))
    pixel_size_m: Mapped[float | None] = mapped_column(Float)
    bounds: Mapped[dict | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    storage_url: Mapped[str | None] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
