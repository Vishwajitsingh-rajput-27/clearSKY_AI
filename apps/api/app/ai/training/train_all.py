from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from app.ai.training.config import TrainingConfig, load_training_config

DEFAULT_MODEL_CONFIGS = {
    "unet-cloud-segmentation": "configs/ai_training.unet_cloud.json",
    "attention-unet": "configs/ai_training.attention_unet.json",
    "swin-unet": "configs/ai_training.swin_unet.json",
    "multi-sensor-fusion": "configs/ai_training.fusion.json",
}

DEFAULT_ORDER = [
    "unet-cloud-segmentation",
    "attention-unet",
    "swin-unet",
    "multi-sensor-fusion",
]


def train_all(
    *,
    model_names: list[str],
    config_paths: dict[str, str],
    device: str | None = None,
    epochs: int | None = None,
    train_manifest: str | None = None,
    val_manifest: str | None = None,
    checkpoint_dir: str | None = None,
    continue_on_error: bool = False,
    validate_best: bool = True,
) -> dict[str, Any]:
    from app.ai.training.train import train_from_config
    from app.ai.training.validate import validate_from_config

    results: dict[str, Any] = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "models": [],
    }

    for model_name in model_names:
        started = time.perf_counter()
        config_path = config_paths[model_name]
        config = load_training_config(config_path)
        config = apply_overrides(
            config,
            device=device,
            epochs=epochs,
            train_manifest=train_manifest,
            val_manifest=val_manifest,
            checkpoint_dir=checkpoint_dir,
        )
        record: dict[str, Any] = {
            "model_name": model_name,
            "config_path": config_path,
            "checkpoint_dir": str(config.checkpoint_path),
            "status": "running",
        }
        results["models"].append(record)

        try:
            train_metrics = train_from_config(config)
            record["train_metrics"] = train_metrics
            if validate_best:
                record["best_checkpoint_metrics"] = validate_from_config(config)
            record["status"] = "completed"
        except Exception as exc:
            record["status"] = "failed"
            record["error"] = str(exc)
            if not continue_on_error:
                record["duration_seconds"] = round(time.perf_counter() - started, 3)
                raise
        finally:
            record["duration_seconds"] = round(time.perf_counter() - started, 3)

    results["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return results


def apply_overrides(
    config: TrainingConfig,
    *,
    device: str | None,
    epochs: int | None,
    train_manifest: str | None,
    val_manifest: str | None,
    checkpoint_dir: str | None,
) -> TrainingConfig:
    updates: dict[str, Any] = {}
    if device:
        updates["device"] = resolve_device(device)
    if epochs is not None:
        updates["epochs"] = epochs
    if train_manifest:
        updates["train_manifest"] = train_manifest
    if val_manifest:
        updates["val_manifest"] = val_manifest
    if checkpoint_dir:
        updates["checkpoint_dir"] = checkpoint_dir
    return replace(config, **updates) if updates else config


def resolve_device(device: str) -> str:
    if device == "auto":
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    return device


def parse_models(value: str) -> list[str]:
    if value == "all":
        return DEFAULT_ORDER

    names = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [name for name in names if name not in DEFAULT_MODEL_CONFIGS]
    if unknown:
        supported = ", ".join(DEFAULT_ORDER)
        raise argparse.ArgumentTypeError(
            f"Unknown model(s): {', '.join(unknown)}. Supported: all,{supported}"
        )
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description="Train all clearSKY AI models sequentially.")
    parser.add_argument(
        "--models",
        type=parse_models,
        default=DEFAULT_ORDER,
        help=(
            "Comma-separated model list or 'all'. Supported: "
            "unet-cloud-segmentation,attention-unet,swin-unet,multi-sensor-fusion"
        ),
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default=None,
        help="Override every config's device. Use 'auto' to prefer CUDA when available.",
    )
    parser.add_argument("--epochs", type=int, default=None, help="Override epochs for every model.")
    parser.add_argument("--train-manifest", default=None, help="Override train manifest path.")
    parser.add_argument("--val-manifest", default=None, help="Override validation manifest path.")
    parser.add_argument("--checkpoint-dir", default=None, help="Override checkpoint root directory.")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue training remaining models when one model fails.",
    )
    parser.add_argument(
        "--skip-best-validation",
        action="store_true",
        help="Skip reloading and validating each best.pt checkpoint after training.",
    )
    parser.add_argument(
        "--summary-path",
        default="models/checkpoints/train_all_summary.json",
        help="Where to write the training summary JSON.",
    )
    args = parser.parse_args()

    results = train_all(
        model_names=args.models,
        config_paths=DEFAULT_MODEL_CONFIGS,
        device=args.device,
        epochs=args.epochs,
        train_manifest=args.train_manifest,
        val_manifest=args.val_manifest,
        checkpoint_dir=args.checkpoint_dir,
        continue_on_error=args.continue_on_error,
        validate_best=not args.skip_best_validation,
    )

    summary_path = Path(args.summary_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
