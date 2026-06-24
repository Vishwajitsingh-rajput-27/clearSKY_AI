from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader

from app.ai.datasets.liss4 import LISS4CloudRemovalDataset, collate_liss4_batch
from app.ai.metrics.losses import CloudSegmentationLoss, ReconstructionLoss
from app.ai.metrics.quality import reconstruction_metrics
from app.ai.models.fusion import MultiSensorFusionNetwork
from app.ai.models.registry import build_model, normalize_model_name
from app.ai.training.config import TrainingConfig, load_training_config, save_training_config


def train_from_config(config: TrainingConfig) -> dict[str, float]:
    device = torch.device(config.device)
    config.checkpoint_path.mkdir(parents=True, exist_ok=True)
    save_training_config(config, config.checkpoint_path / "config.json")

    train_loader = build_loader(config.train_manifest, config=config, split="train", shuffle=True)
    val_loader = build_loader(config.val_manifest, config=config, split="val", shuffle=False)
    model = build_model(
        config.model_name,
        in_channels=4,
        out_channels=3,
        base_channels=config.base_channels,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=1e-4)
    criterion = build_criterion(config).to(device)

    best_val_loss = float("inf")
    latest_metrics: dict[str, float] = {}

    for epoch in range(1, config.epochs + 1):
        train_metrics = run_epoch(
            model,
            train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
        )
        val_metrics = validate(model, val_loader, criterion=criterion, device=device)
        latest_metrics = {f"train_{key}": value for key, value in train_metrics.items()}
        latest_metrics.update({f"val_{key}": value for key, value in val_metrics.items()})
        save_checkpoint(
            config.checkpoint_path / "latest.pt",
            model=model,
            optimizer=optimizer,
            epoch=epoch,
            metrics=latest_metrics,
            config=config,
        )

        if val_metrics["loss_total"] < best_val_loss:
            best_val_loss = val_metrics["loss_total"]
            save_checkpoint(
                config.checkpoint_path / "best.pt",
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                metrics=latest_metrics,
                config=config,
            )

    return latest_metrics


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    *,
    criterion: ReconstructionLoss,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> dict[str, float]:
    model.train()
    totals: dict[str, float] = {}
    batches = 0

    for batch in loader:
        optimizer.zero_grad(set_to_none=True)
        prediction = forward_model(model, batch, device=device)
        target = get_target_for_prediction(prediction, batch, device=device)
        mask = batch["mask"].to(device)
        loss, loss_parts = criterion(prediction, target, mask)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        accumulate(totals, loss_parts)
        batches += 1

    return average(totals, batches)


@torch.no_grad()
def validate(
    model: nn.Module,
    loader: DataLoader,
    *,
    criterion: ReconstructionLoss,
    device: torch.device,
) -> dict[str, float]:
    model.eval()
    totals: dict[str, float] = {}
    batches = 0

    for batch in loader:
        prediction = forward_model(model, batch, device=device)
        target = get_target_for_prediction(prediction, batch, device=device)
        mask = batch["mask"].to(device)
        _, loss_parts = criterion(prediction, target, mask)
        metric_parts = (
            reconstruction_metrics(prediction, target)
            if prediction.shape[1] == 3
            else {}
        )
        accumulate(totals, loss_parts)
        accumulate(totals, metric_parts)
        batches += 1

    return average(totals, batches)


def forward_model(model: nn.Module, batch: dict[str, Any], *, device: torch.device) -> torch.Tensor:
    model_name = normalize_model_name(model.__class__.__name__)

    if isinstance(model, MultiSensorFusionNetwork) or model_name == "multi-sensor-fusion":
        return model(
            batch["model_input"].to(device),
            sentinel1=to_device_or_none(batch.get("sentinel1"), device),
            sentinel2=to_device_or_none(batch.get("sentinel2"), device),
            dem=to_device_or_none(batch.get("dem"), device),
            temporal_refs=to_device_or_none(batch.get("temporal_refs"), device),
        )

    return model(batch["model_input"].to(device))


def build_loader(
    manifest: str,
    *,
    config: TrainingConfig,
    split: str,
    shuffle: bool,
) -> DataLoader:
    dataset = LISS4CloudRemovalDataset(
        manifest,
        patch_size=config.patch_size,
        split=split,
    )
    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=shuffle,
        num_workers=config.num_workers,
        pin_memory=config.device.startswith("cuda"),
        collate_fn=collate_liss4_batch,
    )


def build_criterion(config: TrainingConfig) -> nn.Module:
    if normalize_model_name(config.model_name) == "unet-cloud-segmentation":
        return CloudSegmentationLoss()

    return ReconstructionLoss(
        l1_weight=config.loss_weights.l1,
        spectral_weight=config.loss_weights.spectral,
        edge_weight=config.loss_weights.edge,
        ssim_weight=config.loss_weights.ssim,
    )


def save_checkpoint(
    path: Path,
    *,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: dict[str, float],
    config: TrainingConfig,
) -> None:
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "metrics": metrics,
            "config": {
                **config.__dict__,
                "loss_weights": config.loss_weights.__dict__,
            },
        },
        path,
    )


def to_device_or_none(value: torch.Tensor | None, device: torch.device) -> torch.Tensor | None:
    return None if value is None else value.to(device)


def get_target_for_prediction(
    prediction: torch.Tensor,
    batch: dict[str, Any],
    *,
    device: torch.device,
) -> torch.Tensor:
    return batch["mask"].to(device) if prediction.shape[1] == 1 else batch["target"].to(device)


def accumulate(total: dict[str, float], values: dict[str, float]) -> None:
    for key, value in values.items():
        total[key] = total.get(key, 0.0) + float(value)


def average(total: dict[str, float], batches: int) -> dict[str, float]:
    denominator = max(1, batches)
    return {key: value / denominator for key, value in total.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train clearSKY AI reconstruction models.")
    parser.add_argument(
        "--config",
        default="configs/ai_training.json",
        help="Path to a JSON training config.",
    )
    args = parser.parse_args()
    metrics = train_from_config(load_training_config(args.config))
    print(metrics)


if __name__ == "__main__":
    main()
