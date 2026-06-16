from fastapi import APIRouter, Request
from sqlalchemy import text

from app.core.config import settings
from app.core.responses import api_success
from app.db.session import engine
from app.schemas.health import DependencyStatus, HealthResponse, ReadinessResponse
from app.schemas.responses import ApiResponse
from app.services.cloudinary_client import get_cloudinary_status
from app.services.storage import get_storage_status

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthResponse])
def health_check(request: Request):
    data = HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )
    return api_success(data, request=request)


@router.get("/ready", response_model=ApiResponse[ReadinessResponse])
def readiness_check(request: Request):
    database_status = DependencyStatus(name="database", ok=False, detail="not checked")

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = DependencyStatus(name="database", ok=True, detail="connected")
    except Exception as exc:  # pragma: no cover - environment-specific diagnostic
        database_status = DependencyStatus(name="database", ok=False, detail=str(exc))

    upload_dir_status = DependencyStatus(
        name="upload_dir",
        ok=settings.upload_dir.exists() and settings.upload_dir.is_dir(),
        detail=str(settings.upload_dir),
    )

    dependencies = [
        database_status,
        upload_dir_status,
        get_cloudinary_status(),
        get_storage_status(),
    ]

    data = ReadinessResponse(
        status="ok" if all(dependency.ok for dependency in dependencies) else "degraded",
        service=settings.app_name,
        environment=settings.app_env,
        dependencies=dependencies,
    )
    return api_success(data, request=request)
