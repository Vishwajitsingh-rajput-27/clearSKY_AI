from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.models.model_registry import (
    ExperimentMetric,
    ExperimentRun,
    ModelCheckpoint,
    ModelRegistry,
)
from app.schemas.model_registry import (
    ExperimentMetricResponse,
    ExperimentRunResponse,
    ModelCheckpointResponse,
    ModelRegistryResponse,
    ModelRegistrySummaryResponse,
)
from app.schemas.responses import ApiResponse
from app.services.model_registry import (
    build_summary,
    checkpoint_to_response,
    ensure_model_registry_seeded,
    experiment_to_response,
    metric_to_response,
    model_to_response,
    select_best_model,
)

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/summary", response_model=ApiResponse[ModelRegistrySummaryResponse])
def registry_summary(request: Request, db: DbSession):
    ensure_model_registry_seeded(db)
    return api_success(
        build_summary(db),
        request=request,
        message="Model registry summary retrieved.",
    )


@router.get("/models", response_model=ApiResponse[list[ModelRegistryResponse]])
def list_models(
    request: Request,
    db: DbSession,
    include_inactive: bool = False,
):
    ensure_model_registry_seeded(db)
    statement = select(ModelRegistry).order_by(
        ModelRegistry.is_best.desc(),
        ModelRegistry.name.asc(),
        ModelRegistry.version.desc(),
    )
    if not include_inactive:
        statement = statement.where(ModelRegistry.is_active.is_(True))

    rows = db.scalars(statement).all()
    return api_success(
        [model_to_response(row) for row in rows],
        request=request,
        message="Registered models retrieved.",
    )


@router.get("/models/best", response_model=ApiResponse[ModelRegistryResponse | None])
def get_best_model(request: Request, db: DbSession):
    ensure_model_registry_seeded(db)
    rows = list(db.scalars(select(ModelRegistry)).all())
    best_model = select_best_model(rows)
    return api_success(
        model_to_response(best_model) if best_model else None,
        request=request,
        message="Best model selection retrieved.",
    )


@router.get("/models/{model_id}", response_model=ApiResponse[ModelRegistryResponse | None])
def get_model(model_id: UUID, request: Request, db: DbSession):
    ensure_model_registry_seeded(db)
    row = db.get(ModelRegistry, model_id)
    return api_success(
        model_to_response(row) if row else None,
        request=request,
        message="Registered model retrieved.",
    )


@router.get("/experiments", response_model=ApiResponse[list[ExperimentRunResponse]])
def list_experiments(
    request: Request,
    db: DbSession,
    limit: int = 50,
):
    ensure_model_registry_seeded(db)
    bounded_limit = max(1, min(limit, 200))
    rows = db.scalars(
        select(ExperimentRun)
        .order_by(
            ExperimentRun.is_best.desc(),
            ExperimentRun.training_date.desc().nulls_last(),
            ExperimentRun.created_at.desc(),
        )
        .limit(bounded_limit)
    ).all()
    return api_success(
        [experiment_to_response(row) for row in rows],
        request=request,
        message="Experiment runs retrieved.",
    )


@router.get("/training-history", response_model=ApiResponse[list[ExperimentRunResponse]])
def training_history(request: Request, db: DbSession, limit: int = 50):
    ensure_model_registry_seeded(db)
    bounded_limit = max(1, min(limit, 200))
    rows = db.scalars(
        select(ExperimentRun)
        .order_by(
            ExperimentRun.training_date.desc().nulls_last(),
            ExperimentRun.created_at.desc(),
        )
        .limit(bounded_limit)
    ).all()
    return api_success(
        [experiment_to_response(row) for row in rows],
        request=request,
        message="Training history retrieved.",
    )


@router.get("/metrics-history", response_model=ApiResponse[list[ExperimentMetricResponse]])
def metrics_history(request: Request, db: DbSession, limit: int = 100):
    ensure_model_registry_seeded(db)
    bounded_limit = max(1, min(limit, 500))
    rows = db.scalars(
        select(ExperimentMetric)
        .order_by(
            ExperimentMetric.recorded_at.desc().nulls_last(),
            ExperimentMetric.created_at.desc(),
        )
        .limit(bounded_limit)
    ).all()
    return api_success(
        [metric_to_response(row) for row in rows],
        request=request,
        message="Metric history retrieved.",
    )


@router.get("/checkpoints", response_model=ApiResponse[list[ModelCheckpointResponse]])
def list_checkpoints(request: Request, db: DbSession, limit: int = 100):
    ensure_model_registry_seeded(db)
    bounded_limit = max(1, min(limit, 500))
    rows = db.scalars(
        select(ModelCheckpoint)
        .order_by(
            ModelCheckpoint.is_best.desc(),
            ModelCheckpoint.created_at.desc(),
        )
        .limit(bounded_limit)
    ).all()
    return api_success(
        [checkpoint_to_response(row) for row in rows],
        request=request,
        message="Model checkpoints retrieved.",
    )
