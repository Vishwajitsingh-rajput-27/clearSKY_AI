from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.benchmark import BenchmarkResult
from app.models.inference import InferenceRun
from app.models.user import User
from app.schemas.benchmarks import BenchmarkModelRow, EvaluationMetricsResponse
from app.schemas.inference import InferenceMetrics, InferenceRunResponse, RasterMetadataResponse
from app.services.inference import InferencePipelineResult
from app.services.users import add_storage_usage


def persist_inference_result(
    db: Session,
    result: InferencePipelineResult,
    *,
    status: str = "completed",
    user: User | None = None,
    project_id: UUID | None = None,
) -> InferenceRun:
    additional_storage_bytes = sum(product.stored.file_size_bytes for product in result.products)
    add_storage_usage(
        db,
        user,
        additional_bytes=additional_storage_bytes,
        project_id=project_id,
    )
    inference_run = InferenceRun(
        id=result.run_id,
        user_id=user.id if user else None,
        project_id=project_id,
        status=status,
        original_filename=result.original_filename,
        requested_model=result.requested_model,
        used_model=result.used_model,
        fallback_used=result.fallback_used,
        original_image_url=result.original_image_url,
        cloud_mask_url=result.cloud_mask_url,
        shadow_mask_url=result.shadow_mask_url,
        reconstructed_image_url=result.reconstructed_image_url,
        difference_map_url=result.difference_map_url,
        attention_map_url=result.attention_map_url,
        confidence_map_url=result.confidence_map_url,
        analysis_geotiff_url=result.analysis_geotiff_url,
        qgis_manifest_url=result.qgis_manifest_url,
        cloud_coverage_percent=result.cloud_coverage_percent,
        shadow_coverage_percent=result.shadow_coverage_percent,
        quality_score=result.quality_score,
        reconstruction_confidence_score=result.reconstruction_confidence_score,
        processing_time_seconds=result.processing_time_seconds,
        metrics=result.metrics,
        recommendations=result.recommendations,
        metadata_json=result.metadata,
    )
    db.add(inference_run)

    for product in result.products:
        db.add(
            Asset(
                id=product.asset_id,
                user_id=user.id if user else None,
                project_id=project_id,
                inference_run_id=result.run_id,
                asset_type=product.asset_type,
                storage_url=product.storage.storage_url,
                local_path=product.storage.local_path,
                storage_provider=product.storage.storage_provider,
                external_id=product.storage.external_id,
                filename=product.safe_filename,
                file_size_bytes=product.stored.file_size_bytes,
                mime_type=product.stored.content_type,
                checksum=product.stored.checksum_sha256,
            )
        )

    db.add(
        BenchmarkResult(
            inference_run_id=result.run_id,
            metric_mode=result.evaluation_mode,
            requested_model=result.requested_model,
            used_model=result.used_model,
            psnr=result.evaluation_metrics.get("psnr"),
            ssim=result.evaluation_metrics.get("ssim"),
            rmse=result.evaluation_metrics.get("rmse"),
            mae=result.evaluation_metrics.get("mae"),
            sam=result.evaluation_metrics.get("sam"),
            spectral_consistency_score=result.evaluation_metrics.get(
                "spectral_consistency_score"
            ),
            cloud_reduction_score=result.evaluation_metrics.get("cloud_reduction_score"),
            no_reference_quality_score=result.evaluation_metrics.get(
                "no_reference_quality_score"
            ),
            processing_time_seconds=result.evaluation_metrics.get("processing_time_seconds"),
            report_json_url=result.evaluation_report_url,
            report_markdown_url=result.evaluation_report_markdown_url,
            metrics=result.evaluation_metrics,
            benchmark_rows=result.benchmark_rows,
            explanation=result.evaluation_explanation,
        )
    )

    return inference_run


def build_inference_response(result: InferencePipelineResult) -> InferenceRunResponse:
    return InferenceRunResponse(
        original_image_url=result.original_image_url,
        cloud_mask_url=result.cloud_mask_url,
        shadow_mask_url=result.shadow_mask_url,
        reconstructed_image_url=result.reconstructed_image_url,
        difference_map_url=result.difference_map_url,
        attention_map_url=result.attention_map_url,
        confidence_map_url=result.confidence_map_url,
        analysis_geotiff_url=result.analysis_geotiff_url,
        qgis_manifest_url=result.qgis_manifest_url,
        cloud_coverage_percent=result.cloud_coverage_percent,
        shadow_coverage_percent=result.shadow_coverage_percent,
        quality_score=result.quality_score,
        reconstruction_confidence_score=result.reconstruction_confidence_score,
        processing_time_seconds=result.processing_time_seconds,
        requested_model=result.requested_model,
        used_model=result.used_model,
        fallback_used=result.fallback_used,
        metrics=InferenceMetrics.model_validate(result.metrics),
        metadata=RasterMetadataResponse.model_validate(result.metadata),
        evaluation_mode=result.evaluation_mode,
        evaluation=EvaluationMetricsResponse.model_validate(result.evaluation_metrics),
        evaluation_explanation=result.evaluation_explanation,
        benchmark_rows=[BenchmarkModelRow.model_validate(row) for row in result.benchmark_rows],
        recommendations=result.recommendations,
        evaluation_report_url=result.evaluation_report_url,
        evaluation_report_markdown_url=result.evaluation_report_markdown_url,
    )


def inference_run_to_response(
    db: Session,
    inference_run: InferenceRun,
) -> InferenceRunResponse:
    benchmark = db.scalars(
        select(BenchmarkResult)
        .where(BenchmarkResult.inference_run_id == inference_run.id)
        .order_by(BenchmarkResult.created_at.desc())
        .limit(1)
    ).first()
    metrics = benchmark.metrics if benchmark else None
    benchmark_rows = benchmark.benchmark_rows if benchmark else []
    explanation = benchmark.explanation if benchmark else {}

    return InferenceRunResponse(
        original_image_url=inference_run.original_image_url,
        cloud_mask_url=inference_run.cloud_mask_url,
        shadow_mask_url=inference_run.shadow_mask_url,
        reconstructed_image_url=inference_run.reconstructed_image_url,
        difference_map_url=inference_run.difference_map_url,
        attention_map_url=inference_run.attention_map_url,
        confidence_map_url=inference_run.confidence_map_url,
        analysis_geotiff_url=inference_run.analysis_geotiff_url,
        qgis_manifest_url=inference_run.qgis_manifest_url,
        cloud_coverage_percent=inference_run.cloud_coverage_percent,
        shadow_coverage_percent=inference_run.shadow_coverage_percent,
        quality_score=inference_run.quality_score,
        reconstruction_confidence_score=inference_run.reconstruction_confidence_score,
        processing_time_seconds=inference_run.processing_time_seconds,
        requested_model=inference_run.requested_model,
        used_model=inference_run.used_model,
        fallback_used=inference_run.fallback_used,
        metrics=InferenceMetrics.model_validate(inference_run.metrics or {}),
        metadata=RasterMetadataResponse.model_validate(inference_run.metadata_json or {}),
        evaluation_mode=benchmark.metric_mode if benchmark else None,
        evaluation=EvaluationMetricsResponse.model_validate(metrics or {})
        if metrics is not None
        else None,
        evaluation_explanation=explanation or {},
        benchmark_rows=[BenchmarkModelRow.model_validate(row) for row in benchmark_rows],
        recommendations=inference_run.recommendations or [],
        evaluation_report_url=benchmark.report_json_url if benchmark else None,
        evaluation_report_markdown_url=benchmark.report_markdown_url if benchmark else None,
    )
