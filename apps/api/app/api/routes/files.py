from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.asset import Asset
from app.utils.files import ensure_child_path

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/{asset_id}", response_model=None)
def serve_asset(asset_id: UUID, db: DbSession) -> FileResponse | RedirectResponse:
    asset = db.get(Asset, asset_id)

    if asset is None:
        raise AppError("Asset not found.", status_code=404, code="asset_not_found")

    if asset.storage_provider != "local":
        return RedirectResponse(asset.storage_url)

    if not settings.served_files_enabled:
        raise AppError(
            "Local file serving is disabled.",
            status_code=404,
            code="file_serving_disabled",
        )

    if not asset.local_path:
        raise AppError("Asset not found.", status_code=404, code="asset_not_found")

    file_path = resolve_local_asset_path(Path(asset.local_path))

    if not file_path.exists() or not file_path.is_file():
        raise AppError("Asset file is missing.", status_code=404, code="asset_file_missing")

    return FileResponse(
        path=file_path,
        media_type=asset.mime_type or "application/octet-stream",
        filename=asset.filename,
    )


def resolve_local_asset_path(local_path: Path) -> Path:
    for storage_root in (settings.upload_dir, settings.inference_dir):
        try:
            return ensure_child_path(storage_root, local_path)
        except AppError:
            continue

    raise AppError("Requested file path is outside the storage root.", code="invalid_file_path")
