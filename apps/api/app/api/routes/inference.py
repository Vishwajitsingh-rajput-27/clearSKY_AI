from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.core.security import get_optional_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.inference import InferenceRunResponse
from app.schemas.responses import ApiResponse
from app.services.inference import run_baseline_inference
from app.services.inference_records import build_inference_response, persist_inference_result
from app.services.users import ensure_user_project

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
OptionalUser = Annotated[User | None, Depends(get_optional_current_user)]
InferenceFile = Annotated[UploadFile, File(...)]
RequestedModel = Annotated[str, Form()]
TargetFile = Annotated[UploadFile | None, File()]
ProjectForm = Annotated[UUID | None, Form()]


@router.post(
    "/run",
    response_model=ApiResponse[InferenceRunResponse],
    status_code=status.HTTP_201_CREATED,
)
async def run_inference(
    request: Request,
    file: InferenceFile,
    db: DbSession,
    current_user: OptionalUser = None,
    requested_model: RequestedModel = "opencv-baseline",
    target: TargetFile = None,
    project_id: ProjectForm = None,
):
    project = ensure_user_project(db, current_user, project_id) if current_user else None
    result = await run_baseline_inference(
        file,
        requested_model=requested_model,
        target_file=target,
    )

    persist_inference_result(
        db,
        result,
        user=current_user,
        project_id=project.id if project else None,
    )
    db.commit()
    response = build_inference_response(result)

    return api_success(response, request=request, message="Baseline inference completed.")
