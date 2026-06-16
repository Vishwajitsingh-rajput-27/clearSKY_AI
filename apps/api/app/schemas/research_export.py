from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

ReportFormat = Literal["json", "markdown", "csv", "pdf"]
ResearchReportType = Literal[
    "experiment_report",
    "benchmark_report",
    "metrics_comparison",
    "complete_research_report",
]


class ResearchExportRequest(BaseModel):
    report_type: ResearchReportType = "complete_research_report"
    formats: list[ReportFormat] = Field(default_factory=lambda: ["pdf", "csv"])
    project_id: UUID | None = None


class ResearchMetricComparisonRow(BaseModel):
    source: str
    model_name: str
    version: str | None = None
    dataset_version: str | None = None
    status: str | None = None
    checkpoint_status: str | None = None
    quality_score: float | None = None
    spectral_consistency_score: float | None = None
    cloud_reduction_score: float | None = None
    ssim: float | None = None
    sam: float | None = None
    runtime_seconds: float | None = None


class ResearchExportFileResponse(BaseModel):
    filename: str
    format: ReportFormat
    mime_type: str
    asset_type: str
    storage_url: str
    file_size_bytes: int


class ResearchExportResponse(BaseModel):
    export_id: UUID
    report_type: ResearchReportType
    generated_at: datetime
    files: list[ResearchExportFileResponse]


class ResearchDashboardSummaryResponse(BaseModel):
    generated_at: datetime
    registered_models: int
    active_models: int
    experiment_count: int
    benchmark_count: int
    checkpoint_count: int
    best_model_name: str | None = None
    best_model_version: str | None = None
    best_quality_score: float | None = None
    latest_training_date: datetime | None = None
    model_comparison: list[ResearchMetricComparisonRow]
    chart_series: list[dict[str, Any]]
