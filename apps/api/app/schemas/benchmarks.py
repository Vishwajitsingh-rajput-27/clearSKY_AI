from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationMetricsResponse(BaseModel):
    psnr: float | None = None
    ssim: float | None = None
    rmse: float | None = None
    mae: float | None = None
    sam: float | None = None
    spectral_consistency_score: float | None = Field(default=None, ge=0, le=100)
    cloud_reduction_score: float | None = Field(default=None, ge=0, le=100)
    no_reference_quality_score: float | None = Field(default=None, ge=0, le=100)
    processing_time_seconds: float | None = None


class BenchmarkModelRow(BaseModel):
    model_key: str
    model_name: str
    inputs: str
    requested: bool = False
    used: bool = False
    fallback_used: bool = False
    simulated: bool = False
    quality_score: float = Field(ge=0, le=100)
    spectral_consistency_score: float = Field(ge=0, le=100)
    cloud_reduction_score: float = Field(ge=0, le=100)
    ssim: float = Field(ge=0, le=1)
    sam: float | None = None
    runtime_seconds: float


class BenchmarkResultResponse(BaseModel):
    id: UUID
    inference_run_id: UUID
    metric_mode: str
    requested_model: str
    used_model: str
    metrics: EvaluationMetricsResponse
    benchmark_rows: list[BenchmarkModelRow]
    explanation: dict[str, str] = Field(default_factory=dict)
    report_json_url: str | None = None
    report_markdown_url: str | None = None
    created_at: datetime | None = None
