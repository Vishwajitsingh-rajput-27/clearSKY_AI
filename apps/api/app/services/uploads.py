import hashlib
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import AppError
from app.utils.files import safe_filename

CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class StoredUpload:
    original_filename: str
    safe_filename: str
    local_path: Path
    file_size_bytes: int
    checksum_sha256: str
    content_type: str | None


async def save_upload_file(upload_file: UploadFile, *, scene_id: str) -> StoredUpload:
    original_filename = upload_file.filename or ""
    filename = safe_filename(original_filename)

    scene_dir = settings.upload_dir / scene_id
    scene_dir.mkdir(parents=True, exist_ok=True)
    local_path = scene_dir / filename

    file_size = 0
    checksum = hashlib.sha256()

    try:
        with local_path.open("wb") as target:
            while chunk := await upload_file.read(CHUNK_SIZE):
                file_size += len(chunk)

                if file_size > settings.max_upload_bytes:
                    raise AppError(
                        "Uploaded file exceeds configured size limit.",
                        code="upload_too_large",
                        details={
                            "max_upload_size_mb": settings.max_upload_size_mb,
                            "filename": original_filename,
                        },
                    )

                checksum.update(chunk)
                target.write(chunk)
    except Exception:
        if local_path.exists():
            local_path.unlink()
        raise
    finally:
        await upload_file.close()

    if file_size == 0:
        local_path.unlink(missing_ok=True)
        raise AppError("Uploaded file is empty.", code="empty_upload")

    return StoredUpload(
        original_filename=original_filename,
        safe_filename=filename,
        local_path=local_path,
        file_size_bytes=file_size,
        checksum_sha256=checksum.hexdigest(),
        content_type=upload_file.content_type,
    )
