from pydantic import BaseModel, Field

from app.schemas.benchmarks import BenchmarkModelRow, EvaluationMetricsResponse


class RasterMetadataResponse(BaseModel):
    file_type: str | None = None
    driver: str | None = None
    width: int | None = None
    height: int | None = None
    band_count: int | None = None
    dtype: str | None = None
    crs: str | None = None
    transform: list[float] | None = None
    bounds: list[float] | None = None
    nodata: float | int | None = None
    is_geospatial: bool = False
    reader: str | None = None


class InferenceMetrics(BaseModel):
    cloud_coverage_percent: float = Field(ge=0, le=100)
    shadow_coverage_percent: float = Field(ge=0, le=100)
    quality_score: float = Field(ge=0, le=100)
    reconstruction_confidence_score: float | None = Field(default=None, ge=0, le=100)
    mean_absolute_difference: float
    mask_coverage_percent: float = Field(ge=0, le=100)
    input_width: int
    input_height: int
    processed_width: int
    processed_height: int
    tile_count: int | None = None


class AIRecommendationResponse(BaseModel):
    title: str
    message: str
    severity: str = "info"
    rationale: str
    recommended_inputs: list[str] = Field(default_factory=list)


class InferenceRunResponse(BaseModel):
    original_image_url: str
    cloud_mask_url: str
    shadow_mask_url: str
    reconstructed_image_url: str
    difference_map_url: str
    attention_map_url: str | None = None
    confidence_map_url: str | None = None
    analysis_geotiff_url: str | None = None
    qgis_manifest_url: str | None = None
    cloud_coverage_percent: float
    shadow_coverage_percent: float
    quality_score: float
    reconstruction_confidence_score: float | None = None
    processing_time_seconds: float
    requested_model: str
    used_model: str
    fallback_used: bool
    metrics: InferenceMetrics
    metadata: RasterMetadataResponse | None = None
    evaluation_mode: str | None = None
    evaluation: EvaluationMetricsResponse | None = None
    evaluation_explanation: dict[str, str] = Field(default_factory=dict)
    benchmark_rows: list[BenchmarkModelRow] = Field(default_factory=list)
    recommendations: list[AIRecommendationResponse] = Field(default_factory=list)
    evaluation_report_url: str | None = None
    evaluation_report_markdown_url: str | None = None
