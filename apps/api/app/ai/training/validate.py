from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from app.ai.models.registry import build_model
from app.ai.training.config import TrainingConfig, load_training_config
from app.ai.training.train import build_criterion, build_loader, validate


def validate_from_config(
    config: TrainingConfig,
    checkpoint_path: Path | None = None,
) -> dict[str, float]:
    device = torch.device(config.device)
    checkpoint = checkpoint_path or config.checkpoint_path / "best.pt"

    if not checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint}")

    model = build_model(
        config.model_name,
        in_channels=4,
        out_channels=3,
        base_channels=config.base_channels,
    ).to(device)
    payload = torch.load(checkpoint, map_location=device)
    model.load_state_dict(payload.get("model_state_dict", payload))

    criterion = build_criterion(config)
    loader = build_loader(config.val_manifest, config=config, split="val", shuffle=False)
    return validate(model, loader, criterion=criterion, device=device)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a clearSKY AI checkpoint.")
    parser.add_argument(
        "--config",
        default="configs/ai_training.json",
        help="Path to a JSON training config.",
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="Optional checkpoint path. Defaults to config checkpoint_dir/model_name/best.pt.",
    )
    args = parser.parse_args()
    metrics = validate_from_config(
        load_training_config(args.config),
        Path(args.checkpoint) if args.checkpoint else None,
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
