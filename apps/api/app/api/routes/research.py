from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.core.security import get_optional_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.research_export import (
    ResearchDashboardSummaryResponse,
    ResearchExportRequest,
    ResearchExportResponse,
)
from app.schemas.responses import ApiResponse
from app.services.research_export import (
    generate_research_export,
    get_research_dashboard_summary,
)

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
OptionalUser = Annotated[User | None, Depends(get_optional_current_user)]


@router.get("/summary", response_model=ApiResponse[ResearchDashboardSummaryResponse])
def research_summary(request: Request, db: DbSession):
    return api_success(
        get_research_dashboard_summary(db),
        request=request,
        message="Research dashboard summary retrieved.",
    )


@router.post(
    "/export",
    response_model=ApiResponse[ResearchExportResponse],
    status_code=status.HTTP_201_CREATED,
)
async def export_research_report(
    payload: ResearchExportRequest,
    request: Request,
    db: DbSession,
    current_user: OptionalUser = None,
):
    export = await generate_research_export(db, payload, user=current_user)
    return api_success(export, request=request, message="Research export generated.")
