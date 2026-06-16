from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.asset import Asset
from app.models.inference import InferenceRun
from app.models.project import Project
from app.models.scene import Scene
from app.models.user import User
from app.schemas.auth import (
    ProjectResponse,
    StorageUsageResponse,
    UserHistoryItem,
    UserHistoryResponse,
    UserResponse,
)


def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        storage_quota_bytes=user.storage_quota_bytes,
        used_storage_bytes=user.used_storage_bytes,
        created_at=user.created_at,
    )


def project_to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        status=project.status,
        storage_used_bytes=project.storage_used_bytes,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def storage_to_response(user: User) -> StorageUsageResponse:
    remaining = max(0, user.storage_quota_bytes - user.used_storage_bytes)
    usage_percent = (
        user.used_storage_bytes / user.storage_quota_bytes * 100
        if user.storage_quota_bytes > 0
        else 100.0
    )
    return StorageUsageResponse(
        storage_quota_bytes=user.storage_quota_bytes,
        used_storage_bytes=user.used_storage_bytes,
        remaining_storage_bytes=remaining,
        usage_percent=round(min(100.0, usage_percent), 3),
    )


def assert_storage_available(user: User, additional_bytes: int) -> None:
    if additional_bytes <= 0:
        return

    if user.used_storage_bytes + additional_bytes > user.storage_quota_bytes:
        raise AppError(
            "User storage quota exceeded.",
            code="storage_quota_exceeded",
            status_code=413,
            details={
                "storage_quota_bytes": user.storage_quota_bytes,
                "used_storage_bytes": user.used_storage_bytes,
                "additional_bytes": additional_bytes,
            },
        )


def add_storage_usage(
    db: Session,
    user: User | None,
    *,
    additional_bytes: int,
    project_id: UUID | None = None,
) -> None:
    if user is None or additional_bytes <= 0:
        return

    assert_storage_available(user, additional_bytes)
    user.used_storage_bytes += additional_bytes

    if project_id:
        project = db.get(Project, project_id)
        if project and project.user_id == user.id:
            project.storage_used_bytes += additional_bytes


def calculate_asset_bytes(assets: list[Asset]) -> int:
    return sum(asset.file_size_bytes or 0 for asset in assets)


def ensure_user_project(db: Session, user: User, project_id: UUID | None) -> Project | None:
    if project_id is None:
        return None

    project = db.get(Project, project_id)
    if project is None or project.user_id != user.id:
        raise AppError("Project not found.", status_code=404, code="project_not_found")

    return project


def build_user_history(db: Session, user: User, *, limit: int = 50) -> UserHistoryResponse:
    bounded_limit = max(1, min(limit, 100))
    items: list[UserHistoryItem] = []

    inference_runs = db.scalars(
        select(InferenceRun)
        .where(InferenceRun.user_id == user.id)
        .order_by(InferenceRun.created_at.desc())
        .limit(bounded_limit)
    ).all()
    scene_rows = db.scalars(
        select(Scene)
        .where(Scene.user_id == user.id)
        .order_by(Scene.created_at.desc())
        .limit(bounded_limit)
    ).all()

    for run in inference_runs:
        storage_bytes = db.scalar(
            select(func.coalesce(func.sum(Asset.file_size_bytes), 0)).where(
                Asset.inference_run_id == run.id
            )
        )
        items.append(
            UserHistoryItem(
                id=run.id,
                kind="inference",
                title=run.original_filename,
                status=run.status,
                project_id=run.project_id,
                model=run.used_model,
                quality_score=run.quality_score,
                storage_bytes=int(storage_bytes or 0),
                created_at=run.created_at,
                metadata={
                    "cloud_coverage_percent": run.cloud_coverage_percent,
                    "shadow_coverage_percent": run.shadow_coverage_percent,
                    "fallback_used": run.fallback_used,
                },
            )
        )

    for scene in scene_rows:
        items.append(
            UserHistoryItem(
                id=scene.id,
                kind="scene",
                title=scene.original_filename or scene.filename,
                status=scene.status,
                project_id=scene.project_id,
                storage_bytes=scene.file_size_bytes or 0,
                created_at=scene.created_at,
                metadata={
                    "sensor": scene.sensor,
                    "content_type": scene.content_type,
                    "storage_url": scene.storage_url,
                },
            )
        )

    items = sorted(
        items,
        key=lambda item: item.created_at.isoformat() if item.created_at else "",
        reverse=True,
    )[:bounded_limit]

    return UserHistoryResponse(items=items, storage=storage_to_response(user))
