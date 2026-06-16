from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import cloudinary.uploader
import httpx

from app.core.config import settings
from app.core.exceptions import AppError
from app.schemas.health import DependencyStatus
from app.services.cloudinary_client import configure_cloudinary
from app.services.uploads import StoredUpload


@dataclass(frozen=True)
class StorageResult:
    storage_provider: str
    storage_url: str
    local_path: str | None
    external_id: str | None


def build_local_asset_url(asset_id: UUID) -> str:
    path = f"/api/files/{asset_id}"
    if settings.public_backend_url:
        return f"{settings.public_backend_url}{path}"
    return path


async def persist_upload(
    stored: StoredUpload,
    *,
    scene_id: UUID,
    asset_id: UUID,
) -> StorageResult:
    if settings.storage_provider == "local":
        return StorageResult(
            storage_provider="local",
            storage_url=build_local_asset_url(asset_id),
            local_path=str(stored.local_path),
            external_id=None,
        )

    if settings.storage_provider == "cloudinary":
        return upload_to_cloudinary(stored, scene_id=scene_id)

    if settings.storage_provider == "supabase":
        return await upload_to_supabase(stored, scene_id=scene_id)

    raise AppError(
        "Unsupported storage provider.",
        code="unsupported_storage_provider",
        details={"storage_provider": settings.storage_provider},
    )


def upload_to_cloudinary(stored: StoredUpload, *, scene_id: UUID) -> StorageResult:
    configure_cloudinary()

    public_id = f"clearsky/uploads/{scene_id}/{Path(stored.safe_filename).stem}"

    try:
        result = cloudinary.uploader.upload(
            str(stored.local_path),
            resource_type="raw",
            public_id=public_id,
            overwrite=True,
            use_filename=False,
            unique_filename=False,
        )
    except Exception as exc:  # pragma: no cover - provider-specific network behavior
        raise AppError(
            "Cloudinary upload failed.",
            code="cloudinary_upload_failed",
            details=str(exc),
        ) from exc

    secure_url = result.get("secure_url")
    external_id = result.get("public_id")

    if not secure_url:
        raise AppError("Cloudinary did not return a file URL.", code="cloudinary_url_missing")

    stored.local_path.unlink(missing_ok=True)

    return StorageResult(
        storage_provider="cloudinary",
        storage_url=secure_url,
        local_path=None,
        external_id=external_id,
    )


async def upload_to_supabase(stored: StoredUpload, *, scene_id: UUID) -> StorageResult:
    bucket = settings.supabase_storage_bucket
    object_path = f"uploads/{scene_id}/{stored.safe_filename}"
    supabase_url = settings.supabase_url.rstrip("/")
    endpoint = f"{supabase_url}/storage/v1/object/{bucket}/{object_path}"

    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "content-type": stored.content_type or "application/octet-stream",
        "x-upsert": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                content=stored.local_path.read_bytes(),
            )
    except Exception as exc:  # pragma: no cover - provider-specific network behavior
        raise AppError(
            "Supabase Storage upload failed.",
            code="supabase_upload_failed",
            details=str(exc),
        ) from exc

    if response.status_code not in {200, 201}:
        raise AppError(
            "Supabase Storage upload failed.",
            code="supabase_upload_failed",
            details={
                "status_code": response.status_code,
                "response": response.text[:500],
            },
        )

    stored.local_path.unlink(missing_ok=True)

    return StorageResult(
        storage_provider="supabase",
        storage_url=f"{supabase_url}/storage/v1/object/public/{bucket}/{object_path}",
        local_path=None,
        external_id=f"{bucket}/{object_path}",
    )


def get_storage_status() -> DependencyStatus:
    provider = settings.storage_provider
    ok = True
    detail = "local filesystem"

    if provider == "cloudinary":
        ok = settings.cloudinary_configured
        detail = "configured" if ok else "missing Cloudinary credentials"
    elif provider == "supabase":
        ok = settings.supabase_configured
        detail = (
            f"bucket={settings.supabase_storage_bucket}"
            if ok
            else "missing Supabase URL or service role key"
        )

    return DependencyStatus(name="storage", ok=ok, detail=f"{provider}: {detail}")
