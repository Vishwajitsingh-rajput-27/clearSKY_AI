from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.models.benchmark import BenchmarkResult
from app.schemas.benchmarks import (
    BenchmarkModelRow,
    BenchmarkResultResponse,
    EvaluationMetricsResponse,
)
from app.schemas.responses import ApiResponse

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=ApiResponse[list[BenchmarkResultResponse]])
def list_benchmarks(
    request: Request,
    db: DbSession,
    limit: int = 20,
):
    bounded_limit = max(1, min(limit, 100))
    rows = db.scalars(
        select(BenchmarkResult)
        .order_by(BenchmarkResult.created_at.desc())
        .limit(bounded_limit)
    ).all()
    return api_success(
        [benchmark_to_response(row) for row in rows],
        request=request,
        message="Benchmark results retrieved.",
    )


@router.get("/latest", response_model=ApiResponse[BenchmarkResultResponse | None])
def latest_benchmark(request: Request, db: DbSession):
    row = db.scalars(
        select(BenchmarkResult).order_by(BenchmarkResult.created_at.desc()).limit(1)
    ).first()
    return api_success(
        benchmark_to_response(row) if row else None,
        request=request,
        message="Latest benchmark result retrieved.",
    )


@router.get("/{benchmark_id}", response_model=ApiResponse[BenchmarkResultResponse | None])
def get_benchmark(
    benchmark_id: UUID,
    request: Request,
    db: DbSession,
):
    row = db.get(BenchmarkResult, benchmark_id)
    return api_success(
        benchmark_to_response(row) if row else None,
        request=request,
        message="Benchmark result retrieved.",
    )


def benchmark_to_response(row: BenchmarkResult) -> BenchmarkResultResponse:
    metrics = row.metrics or {
        "psnr": row.psnr,
        "ssim": row.ssim,
        "rmse": row.rmse,
        "mae": row.mae,
        "sam": row.sam,
        "spectral_consistency_score": row.spectral_consistency_score,
        "cloud_reduction_score": row.cloud_reduction_score,
        "no_reference_quality_score": row.no_reference_quality_score,
        "processing_time_seconds": row.processing_time_seconds,
    }
    return BenchmarkResultResponse(
        id=row.id,
        inference_run_id=row.inference_run_id,
        metric_mode=row.metric_mode,
        requested_model=row.requested_model,
        used_model=row.used_model,
        metrics=EvaluationMetricsResponse.model_validate(metrics),
        benchmark_rows=[
            BenchmarkModelRow.model_validate(item) for item in (row.benchmark_rows or [])
        ],
        explanation=row.explanation or {},
        report_json_url=row.report_json_url,
        report_markdown_url=row.report_markdown_url,
        created_at=row.created_at,
    )
