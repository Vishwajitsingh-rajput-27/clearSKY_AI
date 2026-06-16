from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.responses import api_success
from app.core.security import get_optional_current_user
from app.db.session import get_db
from app.models.job import Job
from app.models.scene import Scene
from app.models.user import User
from app.schemas.jobs import JobCreateRequest, JobResponse
from app.schemas.responses import ApiResponse
from app.services.users import ensure_user_project

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
OptionalUser = Annotated[User | None, Depends(get_optional_current_user)]


@router.get("", response_model=ApiResponse[list[JobResponse]])
def list_jobs(
    request: Request,
    db: DbSession,
    current_user: OptionalUser = None,
    limit: int = 50,
    offset: int = 0,
):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    statement = select(Job).order_by(Job.created_at.desc()).limit(limit).offset(offset)
    if current_user:
        statement = statement.where(Job.user_id == current_user.id)
    jobs = db.scalars(statement).all()
    return api_success([JobResponse.model_validate(job) for job in jobs], request=request)


@router.post("", response_model=ApiResponse[JobResponse], status_code=status.HTTP_202_ACCEPTED)
def create_job(
    payload: JobCreateRequest,
    request: Request,
    db: DbSession,
    current_user: OptionalUser = None,
):
    scene = db.get(Scene, payload.scene_id)

    if scene is None:
        raise AppError("Scene not found.", status_code=404, code="scene_not_found")

    if current_user and scene.user_id and scene.user_id != current_user.id:
        raise AppError("Scene not found.", status_code=404, code="scene_not_found")

    project = ensure_user_project(db, current_user, payload.project_id) if current_user else None
    job = Job(
        id=payload.client_job_id,
        user_id=current_user.id if current_user else None,
        project_id=project.id if project else scene.project_id,
        scene_id=payload.scene_id,
        status="queued",
        selected_mode=payload.selected_mode,
        selected_model=payload.selected_model,
        progress=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return api_success(JobResponse.model_validate(job), request=request, message="Job queued.")


@router.get("/{job_id}", response_model=ApiResponse[JobResponse])
def get_job(
    job_id: UUID,
    request: Request,
    db: DbSession,
    current_user: OptionalUser = None,
):
    job = db.get(Job, job_id)

    if job is None:
        raise AppError("Job not found.", status_code=404, code="job_not_found")

    if current_user and job.user_id and job.user_id != current_user.id:
        raise AppError("Job not found.", status_code=404, code="job_not_found")

    return api_success(JobResponse.model_validate(job), request=request)
