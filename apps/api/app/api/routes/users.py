from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import StorageUsageResponse, UserHistoryResponse
from app.schemas.responses import ApiResponse
from app.services.users import build_user_history, storage_to_response

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/me/history", response_model=ApiResponse[UserHistoryResponse])
def my_history(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = 50,
):
    return api_success(
        build_user_history(db, current_user, limit=limit),
        request=request,
        message="User history retrieved.",
    )


@router.get("/me/storage", response_model=ApiResponse[StorageUsageResponse])
def my_storage(request: Request, current_user: CurrentUser):
    return api_success(
        storage_to_response(current_user),
        request=request,
        message="Storage usage retrieved.",
    )
