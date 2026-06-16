import csv
import hashlib
import json
import textwrap
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.asset import Asset
from app.models.benchmark import BenchmarkResult
from app.models.inference import InferenceRun
from app.models.model_registry import ExperimentRun, ModelCheckpoint, ModelRegistry
from app.models.user import User
from app.schemas.research_export import (
    ReportFormat,
    ResearchDashboardSummaryResponse,
    ResearchExportFileResponse,
    ResearchExportRequest,
    ResearchExportResponse,
    ResearchMetricComparisonRow,
    ResearchReportType,
)
from app.services.model_registry import build_summary, ensure_model_registry_seeded
from app.services.storage import persist_upload
from app.services.uploads import StoredUpload
from app.services.users import add_storage_usage, ensure_user_project

MIME_BY_FORMAT: dict[ReportFormat, str] = {
    "json": "application/json",
    "markdown": "text/markdown",
    "csv": "text/csv",
    "pdf": "application/pdf",
}

EXTENSION_BY_FORMAT: dict[ReportFormat, str] = {
    "json": "json",
    "markdown": "md",
    "csv": "csv",
    "pdf": "pdf",
}


def get_research_dashboard_summary(db: Session) -> ResearchDashboardSummaryResponse:
    payload = build_research_payload(db, "complete_research_report")
    summary = payload["summary"]

    return ResearchDashboardSummaryResponse(
        generated_at=payload["generated_at"],
        registered_models=summary["registered_models"],
        active_models=summary["active_models"],
        experiment_count=summary["experiment_count"],
        benchmark_count=summary["benchmark_count"],
        checkpoint_count=summary["checkpoint_count"],
        best_model_name=summary["best_model_name"],
        best_model_version=summary["best_model_version"],
        best_quality_score=summary["best_quality_score"],
        latest_training_date=summary["latest_training_date"],
        model_comparison=[
            ResearchMetricComparisonRow.model_validate(row)
            for row in payload["model_comparison"]
        ],
        chart_series=payload["chart_series"],
    )


async def generate_research_export(
    db: Session,
    request: ResearchExportRequest,
    *,
    user: User | None = None,
) -> ResearchExportResponse:
    ensure_model_registry_seeded(db)
    project = ensure_user_project(db, user, request.project_id) if user else None

    export_id = uuid4()
    generated_at = datetime.now(UTC)
    report_dir = settings.inference_dir / "research_exports" / str(export_id)
    report_dir.mkdir(parents=True, exist_ok=True)

    formats = normalize_formats(request.formats)
    payload = build_research_payload(db, request.report_type, generated_at=generated_at)
    files: list[ResearchExportFileResponse] = []

    for output_format in formats:
        filename = build_export_filename(request.report_type, output_format)
        path = report_dir / filename

        if output_format == "json":
            path.write_text(json.dumps(json_safe(payload), indent=2), encoding="utf-8")
        elif output_format == "markdown":
            path.write_text(render_markdown_report(payload), encoding="utf-8")
        elif output_format == "csv":
            write_metrics_csv(path, payload["model_comparison"])
        elif output_format == "pdf":
            write_text_pdf(path, render_pdf_lines(payload))

        stored = stored_upload_from_path(
            path,
            original_filename=filename,
            content_type=MIME_BY_FORMAT[output_format],
        )
        asset_id = uuid4()
        storage = await persist_upload(stored, scene_id=export_id, asset_id=asset_id)
        add_storage_usage(
            db,
            user,
            additional_bytes=stored.file_size_bytes,
            project_id=project.id if project else None,
        )
        asset_type = f"research_{request.report_type}_{output_format}"
        db.add(
            Asset(
                id=asset_id,
                user_id=user.id if user else None,
                project_id=project.id if project else None,
                asset_type=asset_type,
                storage_url=storage.storage_url,
                local_path=storage.local_path,
                storage_provider=storage.storage_provider,
                external_id=storage.external_id,
                filename=stored.safe_filename,
                file_size_bytes=stored.file_size_bytes,
                mime_type=stored.content_type,
                checksum=stored.checksum_sha256,
            )
        )
        files.append(
            ResearchExportFileResponse(
                filename=filename,
                format=output_format,
                mime_type=MIME_BY_FORMAT[output_format],
                asset_type=asset_type,
                storage_url=storage.storage_url,
                file_size_bytes=stored.file_size_bytes,
            )
        )

    db.commit()

    return ResearchExportResponse(
        export_id=export_id,
        report_type=request.report_type,
        generated_at=generated_at,
        files=files,
    )


def build_research_payload(
    db: Session,
    report_type: ResearchReportType,
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    ensure_model_registry_seeded(db)

    generated_at = generated_at or datetime.now(UTC)
    summary = build_summary(db)
    models = list(
        db.scalars(
            select(ModelRegistry).order_by(
                ModelRegistry.is_best.desc(),
                ModelRegistry.name.asc(),
            )
        ).all()
    )
    experiments = list(
        db.scalars(
            select(ExperimentRun).order_by(
                ExperimentRun.training_date.desc().nulls_last(),
                ExperimentRun.created_at.desc(),
            )
        ).all()
    )
    checkpoints = list(
        db.scalars(
            select(ModelCheckpoint).order_by(
                ModelCheckpoint.is_best.desc(),
                ModelCheckpoint.created_at.desc(),
            )
        ).all()
    )
    benchmarks = list(
        db.scalars(
            select(BenchmarkResult)
            .order_by(BenchmarkResult.created_at.desc())
            .limit(50)
        ).all()
    )
    inference_runs = list(
        db.scalars(
            select(InferenceRun)
            .order_by(InferenceRun.created_at.desc())
            .limit(50)
        ).all()
    )

    comparison_rows = build_model_comparison_rows(models, experiments, benchmarks)
    chart_series = build_chart_series(comparison_rows)

    return {
        "title": report_title(report_type),
        "report_type": report_type,
        "generated_at": generated_at,
        "summary": {
            "registered_models": summary.registered_models,
            "active_models": summary.active_models,
            "experiment_count": summary.experiment_count,
            "benchmark_count": len(benchmarks),
            "checkpoint_count": summary.checkpoint_count,
            "inference_run_count": len(inference_runs),
            "best_model_name": summary.best_model.model_name if summary.best_model else None,
            "best_model_version": summary.best_model.version if summary.best_model else None,
            "best_quality_score": summary.best_quality_score,
            "latest_training_date": summary.latest_training_date,
        },
        "models": [model_payload(row) for row in models],
        "experiments": [experiment_payload(row) for row in experiments],
        "checkpoints": [checkpoint_payload(row) for row in checkpoints],
        "benchmarks": [benchmark_payload(row) for row in benchmarks],
        "inference_runs": [inference_payload(row) for row in inference_runs],
        "model_comparison": comparison_rows,
        "chart_series": chart_series,
    }


def build_model_comparison_rows(
    models: list[ModelRegistry],
    experiments: list[ExperimentRun],
    benchmarks: list[BenchmarkResult],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for model in models:
        metrics = model.metrics or {}
        rows.append(
            {
                "source": "model_registry",
                "model_name": model.name,
                "version": model.version,
                "dataset_version": model.dataset_version,
                "status": model.stage,
                "checkpoint_status": model.checkpoint_status,
                "quality_score": first_metric(
                    metrics,
                    "no_reference_quality_score",
                    "quality_score",
                ),
                "spectral_consistency_score": first_metric(
                    metrics,
                    "spectral_consistency_score",
                ),
                "cloud_reduction_score": first_metric(metrics, "cloud_reduction_score"),
                "ssim": first_metric(metrics, "ssim", "ssim_proxy"),
                "sam": first_metric(metrics, "sam"),
                "runtime_seconds": first_metric(metrics, "processing_time_seconds"),
            }
        )

    for experiment in experiments:
        metrics = experiment.metrics or {}
        rows.append(
            {
                "source": "experiment",
                "model_name": experiment.model_name,
                "version": experiment.version,
                "dataset_version": experiment.dataset_version,
                "status": experiment.status,
                "checkpoint_status": "available" if experiment.checkpoint_score else "pending",
                "quality_score": experiment.checkpoint_score
                or first_metric(metrics, "no_reference_quality_score", "quality_score"),
                "spectral_consistency_score": first_metric(
                    metrics,
                    "spectral_consistency_score",
                ),
                "cloud_reduction_score": first_metric(metrics, "cloud_reduction_score"),
                "ssim": first_metric(metrics, "ssim"),
                "sam": first_metric(metrics, "sam"),
                "runtime_seconds": first_metric(metrics, "processing_time_seconds"),
            }
        )

    for benchmark in benchmarks:
        for row in benchmark.benchmark_rows or []:
            rows.append(
                {
                    "source": "benchmark",
                    "model_name": row.get("model_name") or row.get("model_key"),
                    "version": None,
                    "dataset_version": benchmark.metric_mode,
                    "status": "used" if row.get("used") else "comparison",
                    "checkpoint_status": "fallback" if row.get("fallback_used") else None,
                    "quality_score": as_float(row.get("quality_score")),
                    "spectral_consistency_score": as_float(
                        row.get("spectral_consistency_score")
                    ),
                    "cloud_reduction_score": as_float(row.get("cloud_reduction_score")),
                    "ssim": as_float(row.get("ssim")),
                    "sam": as_float(row.get("sam")),
                    "runtime_seconds": as_float(row.get("runtime_seconds")),
                }
            )

    return rows


def build_chart_series(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_model: dict[str, dict[str, Any]] = {}

    for row in rows:
        model_name = str(row.get("model_name") or "unknown")
        quality = as_float(row.get("quality_score")) or 0.0
        current = best_by_model.get(model_name)

        if current is None or quality > (as_float(current.get("quality_score")) or 0.0):
            best_by_model[model_name] = row

    return [
        {
            "model": name,
            "quality": as_float(row.get("quality_score")) or 0.0,
            "spectral": as_float(row.get("spectral_consistency_score")) or 0.0,
            "cloud_reduction": as_float(row.get("cloud_reduction_score")) or 0.0,
            "ssim": as_float(row.get("ssim")) or 0.0,
        }
        for name, row in sorted(
            best_by_model.items(),
            key=lambda item: as_float(item[1].get("quality_score")) or 0.0,
            reverse=True,
        )[:12]
    ]


def render_markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Generated at: `{payload['generated_at'].isoformat()}`",
        f"- Report type: `{payload['report_type']}`",
        f"- Registered models: `{summary['registered_models']}`",
        f"- Experiments: `{summary['experiment_count']}`",
        f"- Benchmarks: `{summary['benchmark_count']}`",
        f"- Checkpoints: `{summary['checkpoint_count']}`",
        f"- Best model: `{summary['best_model_name'] or 'n/a'}`",
        "",
        "## Metrics Comparison",
        "",
        "| Source | Model | Version | Quality | Spectral | Cloud Reduction | SSIM | Runtime |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in payload["model_comparison"]:
        lines.append(
            "| {source} | {model_name} | {version} | {quality_score} | "
            "{spectral_consistency_score} | {cloud_reduction_score} | {ssim} | "
            "{runtime_seconds} |".format(**format_row(row))
        )

    if payload["experiments"]:
        lines.extend(["", "## Experiments", ""])
        for experiment in payload["experiments"]:
            lines.append(
                "- `{experiment_name}` `{status}` model=`{model_name}` "
                "dataset=`{dataset_version}` score=`{checkpoint_score}`".format(
                    **format_row(experiment)
                )
            )

    if payload["benchmarks"]:
        lines.extend(["", "## Benchmark Runs", ""])
        for benchmark in payload["benchmarks"]:
            lines.append(
                "- `{id}` used=`{used_model}` mode=`{metric_mode}` "
                "created=`{created_at}`".format(**format_row(benchmark))
            )

    return "\n".join(lines) + "\n"


def render_pdf_lines(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    lines = [
        payload["title"],
        "",
        f"Generated at: {payload['generated_at'].isoformat()}",
        f"Report type: {payload['report_type']}",
        "",
        "Executive Summary",
        f"Registered models: {summary['registered_models']}",
        f"Active models: {summary['active_models']}",
        f"Experiments: {summary['experiment_count']}",
        f"Benchmarks: {summary['benchmark_count']}",
        f"Checkpoints: {summary['checkpoint_count']}",
        f"Best model: {summary['best_model_name'] or 'n/a'}",
        f"Best quality score: {format_value(summary['best_quality_score'])}",
        "",
        "Metrics Comparison",
    ]

    for row in payload["model_comparison"][:30]:
        lines.append(
            "{source}: {model_name} quality={quality_score} spectral={spectral_consistency_score} "
            "cloud={cloud_reduction_score} ssim={ssim}".format(**format_row(row))
        )

    lines.extend(["", "Experiment Notes"])
    for experiment in payload["experiments"][:20]:
        lines.append(
            "{experiment_name} | {model_name} | {status} | dataset={dataset_version} | "
            "score={checkpoint_score}".format(**format_row(experiment))
        )

    lines.extend(["", "Benchmark Notes"])
    for benchmark in payload["benchmarks"][:20]:
        lines.append(
            "{id} | used={used_model} | mode={metric_mode} | created={created_at}".format(
                **format_row(benchmark)
            )
        )

    return lines


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "source",
        "model_name",
        "version",
        "dataset_version",
        "status",
        "checkpoint_status",
        "quality_score",
        "spectral_consistency_score",
        "cloud_reduction_score",
        "ssim",
        "sam",
        "runtime_seconds",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fieldnames})


def write_text_pdf(path: Path, lines: list[str]) -> None:
    wrapped_lines: list[str] = []
    for line in lines:
        if not line:
            wrapped_lines.append("")
            continue

        wrapped_lines.extend(textwrap.wrap(str(line), width=96) or [""])

    pages = [
        wrapped_lines[index : index + 50]
        for index in range(0, max(len(wrapped_lines), 1), 50)
    ]
    objects: dict[int, bytes] = {}
    page_ids = [4 + index * 2 for index in range(len(pages))]

    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[2] = (
        f"<< /Type /Pages /Count {len(page_ids)} /Kids "
        f"[{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] >>"
    ).encode("latin-1")
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    for index, page_lines in enumerate(pages):
        page_id = 4 + index * 2
        content_id = page_id + 1
        stream = render_pdf_page_stream(page_lines)
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("latin-1")
        objects[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream"
        )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = {0: 0}
    for object_id in sorted(objects):
        offsets[object_id] = len(pdf)
        pdf.extend(f"{object_id} 0 obj\n".encode("latin-1"))
        pdf.extend(objects[object_id])
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    size = max(objects) + 1
    pdf.extend(f"xref\n0 {size}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for object_id in range(1, size):
        pdf.extend(f"{offsets.get(object_id, 0):010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "latin-1"
        )
    )
    path.write_bytes(bytes(pdf))


def render_pdf_page_stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 10 Tf", "50 760 Td", "14 TL"]
    for line in lines:
        commands.append(f"({escape_pdf_text(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", "replace")


def escape_pdf_text(value: Any) -> str:
    text = str(value).encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def stored_upload_from_path(
    path: Path,
    *,
    original_filename: str,
    content_type: str,
) -> StoredUpload:
    file_bytes = path.read_bytes()
    return StoredUpload(
        original_filename=original_filename,
        safe_filename=path.name,
        local_path=path,
        file_size_bytes=len(file_bytes),
        checksum_sha256=hashlib.sha256(file_bytes).hexdigest(),
        content_type=content_type,
    )


def normalize_formats(formats: list[ReportFormat]) -> list[ReportFormat]:
    if not formats:
        return ["pdf", "csv"]

    ordered: list[ReportFormat] = []
    for output_format in formats:
        if output_format not in ordered:
            ordered.append(output_format)

    return ordered


def build_export_filename(
    report_type: ResearchReportType,
    output_format: ReportFormat,
) -> str:
    return f"{report_type}.{EXTENSION_BY_FORMAT[output_format]}"


def report_title(report_type: ResearchReportType) -> str:
    titles = {
        "experiment_report": "clearSKY AI Experiment Report",
        "benchmark_report": "clearSKY AI Benchmark Report",
        "metrics_comparison": "clearSKY AI Metrics Comparison Report",
        "complete_research_report": "clearSKY AI Research Export",
    }
    return titles[report_type]


def model_payload(row: ModelRegistry) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "model_name": row.name,
        "version": row.version,
        "architecture": row.architecture,
        "runtime_type": row.runtime_type,
        "dataset_version": row.dataset_version,
        "training_date": row.training_date,
        "metrics": row.metrics or {},
        "checkpoint_path": row.checkpoint_path,
        "checkpoint_status": row.checkpoint_status,
        "stage": row.stage,
        "is_active": row.is_active,
        "is_best": row.is_best,
        "created_at": row.created_at,
    }


def experiment_payload(row: ExperimentRun) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "experiment_name": row.experiment_name,
        "model_name": row.model_name,
        "version": row.version,
        "status": row.status,
        "training_date": row.training_date,
        "dataset_version": row.dataset_version,
        "metrics": row.metrics or {},
        "hyperparameters": row.hyperparameters or {},
        "checkpoint_path": row.checkpoint_path,
        "checkpoint_score": row.checkpoint_score,
        "is_best": row.is_best,
        "notes": row.notes,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "created_at": row.created_at,
    }


def checkpoint_payload(row: ModelCheckpoint) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "model_name": row.model_name,
        "version": row.version,
        "checkpoint_path": row.checkpoint_path,
        "storage_uri": row.storage_uri,
        "status": row.status,
        "epoch": row.epoch,
        "metric_name": row.metric_name,
        "metric_value": row.metric_value,
        "metrics": row.metrics or {},
        "file_size_bytes": row.file_size_bytes,
        "is_best": row.is_best,
        "created_at": row.created_at,
    }


def benchmark_payload(row: BenchmarkResult) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "inference_run_id": str(row.inference_run_id),
        "metric_mode": row.metric_mode,
        "requested_model": row.requested_model,
        "used_model": row.used_model,
        "metrics": row.metrics or {},
        "benchmark_rows": row.benchmark_rows or [],
        "report_json_url": row.report_json_url,
        "report_markdown_url": row.report_markdown_url,
        "created_at": row.created_at,
    }


def inference_payload(row: InferenceRun) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "original_filename": row.original_filename,
        "requested_model": row.requested_model,
        "used_model": row.used_model,
        "fallback_used": row.fallback_used,
        "quality_score": row.quality_score,
        "cloud_coverage_percent": row.cloud_coverage_percent,
        "shadow_coverage_percent": row.shadow_coverage_percent,
        "processing_time_seconds": row.processing_time_seconds,
        "created_at": row.created_at,
    }


def first_metric(metrics: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = as_float(metrics.get(key))
        if value is not None:
            return value

    return None


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int | float):
        return float(value)

    return None


def format_value(value: Any) -> str:
    if value is None:
        return "n/a"

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, float):
        return f"{value:.4f}"

    if isinstance(value, int):
        return str(value)

    return str(value)


def format_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: format_value(value) for key, value in row.items()}


def json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, list):
        return [json_safe(item) for item in value]

    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}

    return value
