from __future__ import annotations

import argparse
import json
import time
import zipfile
from pathlib import Path
from typing import Any

from app.ai.datasets.build_fusion_100 import (
    BuilderConfig,
    build_dataset,
    initialize_earth_engine,
    write_manifests,
)
from app.ai.training.train_all import DEFAULT_ORDER, PROFILE_CONFIGS, parse_models, train_all


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    dataset_config = load_builder_config(args)

    initialize_earth_engine(dataset_config.project, authenticate=args.authenticate)
    print(
        json.dumps(
            {
                "stage": "sentinel_dataset_build_start",
                "project": dataset_config.project,
                "output_dir": str(dataset_config.output_dir),
                "target_count": dataset_config.target_count,
                "image_size": dataset_config.image_size,
                "date_range": [dataset_config.start_date, dataset_config.end_date],
                "dry_run": dataset_config.dry_run,
            },
            indent=2,
        )
    )

    rows = build_dataset(dataset_config)
    if not dataset_config.dry_run:
        write_manifests(rows, dataset_config.output_dir)

    train_manifest = dataset_config.output_dir / "manifests" / "train.json"
    val_manifest = dataset_config.output_dir / "manifests" / "val.json"
    summary_path = Path(args.summary_path) if args.summary_path else default_summary_path(args)
    checkpoint_dir = Path(args.checkpoint_dir)

    if dataset_config.dry_run:
        summary = {
            "dataset": dataset_summary(rows, dataset_config),
            "training": None,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    print(
        json.dumps(
            {
                "stage": "training_start",
                "profile": args.profile,
                "models": args.models,
                "train_manifest": str(train_manifest),
                "val_manifest": str(val_manifest),
                "checkpoint_dir": str(checkpoint_dir),
                "summary_path": str(summary_path),
            },
            indent=2,
        )
    )

    training_results = train_all(
        model_names=args.models,
        config_paths=PROFILE_CONFIGS[args.profile],
        profile=args.profile,
        device=args.device,
        epochs=args.epochs,
        train_manifest=str(train_manifest),
        val_manifest=str(val_manifest),
        checkpoint_dir=str(checkpoint_dir),
        continue_on_error=args.continue_on_error,
        validate_best=not args.skip_best_validation,
    )

    summary = {
        "dataset": dataset_summary(rows, dataset_config),
        "training": training_results,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    if args.archive_path:
        write_archive(
            Path(args.archive_path),
            checkpoint_dir=checkpoint_dir,
            summary_path=summary_path,
            dataset_dir=dataset_config.output_dir,
            include_dataset=args.archive_dataset,
        )
        summary["archive_path"] = args.archive_path
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Sentinel-1/Sentinel-2/DEM fusion dataset with Earth Engine "
            "and train clearSKY AI models."
        )
    )
    parser.add_argument("--config", default="configs/fusion_dataset_100.json")
    parser.add_argument("--project", default=None, help="Google Cloud project for Earth Engine.")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--target-count", type=int, default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--image-size", type=int, default=None)
    parser.add_argument("--chip-size-km", type=float, default=None)
    parser.add_argument("--max-cloud-percent", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--authenticate", action="store_true")
    parser.add_argument("--overwrite-data", action="store_true")
    parser.add_argument(
        "--models",
        type=parse_models,
        default=DEFAULT_ORDER,
        help="Comma-separated model list or 'all'.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_CONFIGS),
        default="fast",
        help="Use 'fast' for quick automatic runs or 'full' for serious longer training.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Training device. 'auto' uses CUDA when available.",
    )
    parser.add_argument("--epochs", type=int, default=None, help="Override epochs for every model.")
    parser.add_argument(
        "--checkpoint-dir",
        default="models/checkpoints_fusion_auto",
        help="Checkpoint root directory.",
    )
    parser.add_argument("--summary-path", default=None, help="Combined dataset+training summary path.")
    parser.add_argument(
        "--archive-path",
        default=None,
        help="Optional .zip path for TeraBox upload. By default archives checkpoints, summary, and manifests.",
    )
    parser.add_argument(
        "--archive-dataset",
        action="store_true",
        help="Also include raw dataset files in the upload archive. This can be very large.",
    )
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--skip-best-validation", action="store_true")
    return parser.parse_args()


def load_builder_config(args: argparse.Namespace) -> BuilderConfig:
    payload: dict[str, Any] = {}
    config_path = Path(args.config)
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))

    overrides = {
        "project": args.project,
        "output_dir": args.output_dir,
        "target_count": args.target_count,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "image_size": args.image_size,
        "chip_size_km": args.chip_size_km,
        "max_cloud_percent": args.max_cloud_percent,
    }
    payload.update({key: value for key, value in overrides.items() if value is not None})

    if args.dry_run:
        payload["dry_run"] = True
    if args.overwrite_data:
        payload["skip_existing"] = False
    if "output_dir" in payload:
        payload["output_dir"] = Path(payload["output_dir"])

    return BuilderConfig(**payload)


def dataset_summary(rows: list[dict[str, Any]], config: BuilderConfig) -> dict[str, Any]:
    return {
        "scene_count": len(rows),
        "output_dir": str(config.output_dir),
        "train_manifest": str(config.output_dir / "manifests" / "train.json"),
        "val_manifest": str(config.output_dir / "manifests" / "val.json"),
        "test_manifest": str(config.output_dir / "manifests" / "test.json"),
        "source": "sentinel-proxy-earth-engine",
    }


def default_summary_path(args: argparse.Namespace) -> Path:
    checkpoint_dir = Path(args.checkpoint_dir)
    model_label = "all" if args.models == DEFAULT_ORDER else "-".join(args.models)
    return checkpoint_dir / f"fusion_pipeline_{args.profile}_{model_label}_summary.json"


def write_archive(
    archive_path: Path,
    *,
    checkpoint_dir: Path,
    summary_path: Path,
    dataset_dir: Path,
    include_dataset: bool,
) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        if checkpoint_dir.exists():
            add_tree(archive, checkpoint_dir, arc_root=Path("checkpoints"))
        if summary_path.exists():
            archive.write(summary_path, Path("summaries") / summary_path.name)

        manifest_dir = dataset_dir / "manifests"
        if manifest_dir.exists():
            add_tree(archive, manifest_dir, arc_root=Path("manifests"))
        if include_dataset and dataset_dir.exists():
            add_tree(archive, dataset_dir / "raw", arc_root=Path("raw"))


def add_tree(archive: zipfile.ZipFile, root: Path, *, arc_root: Path) -> None:
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file():
            archive.write(path, arc_root / path.relative_to(root))


if __name__ == "__main__":
    main()
