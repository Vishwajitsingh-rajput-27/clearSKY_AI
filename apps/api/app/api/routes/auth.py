from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.responses import api_success
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserResponse, UserSignupRequest
from app.schemas.responses import ApiResponse
from app.services.users import user_to_response

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/signup",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
)
def signup(payload: UserSignupRequest, request: Request, db: DbSession):
    existing = db.scalars(select(User).where(User.email == payload.email).limit(1)).first()

    if existing:
        raise AppError(
            "An account already exists for this email.",
            code="email_already_registered",
            status_code=status.HTTP_409_CONFLICT,
        )

    user = User(
        email=payload.email,
        full_name=payload.full_name.strip() if payload.full_name else None,
        password_hash=hash_password(payload.password),
        storage_quota_bytes=settings.default_user_storage_quota_bytes,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token, expires_at = create_access_token(user)
    return api_success(
        TokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            user=user_to_response(user),
        ),
        request=request,
        message="Account created.",
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(payload: UserLoginRequest, request: Request, db: DbSession):
    user = db.scalars(select(User).where(User.email == payload.email).limit(1)).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError(
            "Invalid email or password.",
            code="invalid_credentials",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        raise AppError(
            "User account is inactive.",
            code="inactive_user",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    access_token, expires_at = create_access_token(user)
    return api_success(
        TokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            user=user_to_response(user),
        ),
        request=request,
        message="Login successful.",
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
def me(request: Request, current_user: CurrentUser):
    return api_success(
        user_to_response(current_user),
        request=request,
        message="User profile retrieved.",
    )
