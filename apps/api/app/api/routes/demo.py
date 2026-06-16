from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.schemas.demo import DemoSampleResponse
from app.schemas.responses import ApiResponse
from app.services.demo import get_or_create_demo_sample

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
ForceDemoRun = Annotated[bool, Query()]


@router.get("/sample", response_model=ApiResponse[DemoSampleResponse])
async def get_demo_sample(request: Request, db: DbSession):
    demo = await get_or_create_demo_sample(db, use_cache=True)
    return api_success(demo, request=request, message="Demo sample retrieved.")


@router.post(
    "/run",
    response_model=ApiResponse[DemoSampleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def run_demo(
    request: Request,
    db: DbSession,
    force: ForceDemoRun = False,
):
    demo = await get_or_create_demo_sample(db, use_cache=not force)
    return api_success(demo, request=request, message="Demo pipeline completed.")
