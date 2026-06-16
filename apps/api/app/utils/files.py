import re
import unicodedata
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.exceptions import AppError


def get_original_filename(filename: str | None) -> str:
    if not filename:
        raise AppError("Uploaded file must include a filename.", code="missing_filename")

    return Path(filename).name


def validate_upload_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix not in settings.allowed_upload_extensions:
        raise AppError(
            "Unsupported upload type.",
            code="unsupported_upload_type",
            details={
                "filename": filename,
                "allowed_extensions": settings.allowed_upload_extensions,
            },
        )

    return suffix


def safe_filename(filename: str) -> str:
    original = get_original_filename(filename)
    validate_upload_extension(original)

    normalized = unicodedata.normalize("NFKD", original).encode("ascii", "ignore").decode("ascii")
    stem = Path(normalized).stem.lower()
    suffix = Path(normalized).suffix.lower()
    stem = re.sub(r"[^a-z0-9._-]+", "-", stem).strip(".-_")

    if not stem:
        stem = "scene"

    return f"{stem}-{uuid4().hex[:12]}{suffix}"


def ensure_child_path(parent: Path, child: Path) -> Path:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()

    if parent_resolved != child_resolved and parent_resolved not in child_resolved.parents:
        raise AppError("Requested file path is outside the storage root.", code="invalid_file_path")

    return child_resolved
