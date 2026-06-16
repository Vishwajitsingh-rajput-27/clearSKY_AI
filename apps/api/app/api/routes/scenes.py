from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.responses import api_success
from app.core.security import get_optional_current_user
from app.db.session import get_db
from app.models.asset import Asset
from app.models.scene import Scene
from app.models.user import User
from app.schemas.responses import ApiResponse
from app.schemas.scenes import SceneCreateRequest, SceneResponse
from app.services.storage import persist_upload
from app.services.uploads import save_upload_file
from app.services.users import add_storage_usage, assert_storage_available, ensure_user_project

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
OptionalUser = Annotated[User | None, Depends(get_optional_current_user)]
SceneUploadFile = Annotated[UploadFile, File(...)]
ProjectForm = Annotated[UUID | None, Form()]


@router.get("", response_model=ApiResponse[list[SceneResponse]])
def list_scenes(
    request: Request,
    db: DbSession,
    current_user: OptionalUser = None,
    limit: int = 50,
    offset: int = 0,
):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    statement = select(Scene).order_by(Scene.created_at.desc()).limit(limit).offset(offset)
    if current_user:
        statement = statement.where(Scene.user_id == current_user.id)
    scenes = db.scalars(statement).all()
    return api_success([SceneResponse.model_validate(scene) for scene in scenes], request=request)


@router.post("", response_model=ApiResponse[SceneResponse], status_code=status.HTTP_201_CREATED)
def register_scene(
    payload: SceneCreateRequest,
    request: Request,
    db: DbSession,
    current_user: OptionalUser = None,
):
    project = ensure_user_project(db, current_user, payload.project_id) if current_user else None
    scene = Scene(
        id=payload.client_scene_id,
        user_id=current_user.id if current_user else None,
        project_id=project.id if project else None,
        filename=payload.filename,
        original_filename=payload.filename,
        sensor=payload.sensor,
        status="registered",
    )
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return api_success(
        SceneResponse.model_validate(scene),
        request=request,
        message="Scene registered.",
    )


@router.post(
    "/upload",
    response_model=ApiResponse[SceneResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_scene(
    request: Request,
    file: SceneUploadFile,
    db: DbSession,
    current_user: OptionalUser = None,
    project_id: ProjectForm = None,
):
    project = ensure_user_project(db, current_user, project_id) if current_user else None
    scene_id = uuid4()
    stored = await save_upload_file(file, scene_id=str(scene_id))
    if current_user:
        assert_storage_available(current_user, stored.file_size_bytes)

    asset_id = uuid4()
    storage = await persist_upload(stored, scene_id=scene_id, asset_id=asset_id)

    scene = Scene(
        id=scene_id,
        user_id=current_user.id if current_user else None,
        project_id=project.id if project else None,
        filename=stored.safe_filename,
        original_filename=stored.original_filename,
        safe_filename=stored.safe_filename,
        sensor="LISS-IV",
        status="uploaded",
        content_type=stored.content_type,
        file_size_bytes=stored.file_size_bytes,
        checksum_sha256=stored.checksum_sha256,
        local_path=storage.local_path,
        storage_provider=storage.storage_provider,
        external_id=storage.external_id,
        storage_url=storage.storage_url,
    )
    asset = Asset(
        id=asset_id,
        user_id=current_user.id if current_user else None,
        project_id=project.id if project else None,
        scene_id=scene_id,
        asset_type="original",
        storage_url=storage.storage_url,
        local_path=storage.local_path,
        storage_provider=storage.storage_provider,
        external_id=storage.external_id,
        filename=stored.safe_filename,
        file_size_bytes=stored.file_size_bytes,
        mime_type=stored.content_type,
        checksum=stored.checksum_sha256,
    )

    db.add(scene)
    db.add(asset)
    add_storage_usage(
        db,
        current_user,
        additional_bytes=stored.file_size_bytes,
        project_id=project.id if project else None,
    )
    db.commit()
    db.refresh(scene)

    return api_success(
        SceneResponse.model_validate(scene),
        request=request,
        message="Scene uploaded.",
    )


@router.get("/{scene_id}", response_model=ApiResponse[SceneResponse])
def get_scene(
    scene_id: UUID,
    request: Request,
    db: DbSession,
):
    scene = db.get(Scene, scene_id)

    if scene is None:
        raise AppError("Scene not found.", status_code=404, code="scene_not_found")

    return api_success(SceneResponse.model_validate(scene), request=request)
