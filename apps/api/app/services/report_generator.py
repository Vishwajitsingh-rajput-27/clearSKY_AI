from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID


def generate_evaluation_report(
    *,
    report_dir: Path,
    inference_run_id: UUID,
    original_filename: str,
    requested_model: str,
    used_model: str,
    metric_mode: str,
    metrics: dict[str, float | None],
    benchmark_rows: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "inference_run_id": str(inference_run_id),
        "original_filename": original_filename,
        "requested_model": requested_model,
        "used_model": used_model,
        "metric_mode": metric_mode,
        "metrics": metrics,
        "benchmark_rows": benchmark_rows,
        "metadata": metadata or {},
    }
    json_path = report_dir / "evaluation_report.json"
    markdown_path = report_dir / "evaluation_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
    return json_path, markdown_path


def render_markdown_report(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# clearSKY AI Evaluation Report",
        "",
        f"- Inference run: `{payload['inference_run_id']}`",
        f"- Source file: `{payload['original_filename']}`",
        f"- Requested model: `{payload['requested_model']}`",
        f"- Used model: `{payload['used_model']}`",
        f"- Metric mode: `{payload['metric_mode']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in metrics.items():
        lines.append(f"| {key} | {format_report_value(value)} |")

    lines.extend(
        [
            "",
            "## Model Comparison",
            "",
            "| Model | Inputs | Quality | Spectral | Cloud Reduction | SSIM | Runtime |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["benchmark_rows"]:
        lines.append(
            "| {model_name} | {inputs} | {quality_score} | {spectral_consistency_score} | "
            "{cloud_reduction_score} | {ssim} | {runtime_seconds}s |".format(**row)
        )

    return "\n".join(lines) + "\n"


def format_report_value(value: Any) -> str:
    if value is None:
        return "n/a"

    if isinstance(value, float):
        return f"{value:.4f}"

    return str(value)
