from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LossWeights:
    l1: float = 1.0
    spectral: float = 0.2
    edge: float = 0.1
    ssim: float = 0.5


@dataclass(frozen=True)
class TrainingConfig:
    experiment_name: str = "clearsky_liss4_reconstruction"
    model_name: str = "attention-unet"
    train_manifest: str = "data/manifests/train.json"
    val_manifest: str = "data/manifests/val.json"
    checkpoint_dir: str = "models/checkpoints"
    patch_size: int = 256
    batch_size: int = 4
    epochs: int = 50
    learning_rate: float = 1e-4
    num_workers: int = 2
    device: str = "cpu"
    base_channels: int = 32
    loss_weights: LossWeights = field(default_factory=LossWeights)

    @property
    def checkpoint_path(self) -> Path:
        return Path(self.checkpoint_dir) / self.model_name


def load_training_config(path: str | Path) -> TrainingConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    loss_weights = LossWeights(**data.pop("loss_weights", {}))
    return TrainingConfig(**data, loss_weights=loss_weights)


def save_training_config(config: TrainingConfig, path: str | Path) -> None:
    payload: dict[str, Any] = {
        **config.__dict__,
        "loss_weights": config.loss_weights.__dict__,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
