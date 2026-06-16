from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.responses import api_success
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.auth import ProjectCreateRequest, ProjectResponse
from app.schemas.responses import ApiResponse
from app.services.users import project_to_response

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=ApiResponse[list[ProjectResponse]])
def list_projects(request: Request, db: DbSession, current_user: CurrentUser):
    projects = db.scalars(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    ).all()
    return api_success(
        [project_to_response(project) for project in projects],
        request=request,
        message="Projects retrieved.",
    )


@router.post("", response_model=ApiResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
):
    project = Project(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return api_success(
        project_to_response(project),
        request=request,
        message="Project created.",
    )


@router.get("/{project_id}", response_model=ApiResponse[ProjectResponse])
def get_project(
    project_id: UUID,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
):
    project = db.get(Project, project_id)

    if project is None or project.user_id != current_user.id:
        raise AppError("Project not found.", status_code=404, code="project_not_found")

    return api_success(project_to_response(project), request=request, message="Project retrieved.")
