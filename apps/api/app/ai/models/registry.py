from __future__ import annotations

from pathlib import Path

from torch import nn

from app.ai.models.attention_unet import AttentionUNetReconstructor
from app.ai.models.fusion import MultiSensorFusionNetwork
from app.ai.models.swin_unet import SwinUNetReconstructor
from app.ai.models.unet import UNetCloudSegmenter

SEGMENTATION_ALIASES = {
    "unet",
    "u-net",
    "unet-cloud",
    "unet-cloud-segmentation",
    "cloud-segmentation-unet",
}
ATTENTION_UNET_ALIASES = {"attention-unet", "attention_unet", "att-unet", "attunet"}
SWIN_UNET_ALIASES = {"swin-unet", "swin_unet", "swinunet"}
MULTI_SENSOR_ALIASES = {
    "multi-sensor",
    "multi-sensor-fusion",
    "multisensor",
    "fusion-net",
    "clearsky-fusion",
}


def normalize_model_name(model_name: str) -> str:
    normalized = model_name.strip().lower().replace("_", "-")

    if normalized in SEGMENTATION_ALIASES:
        return "unet-cloud-segmentation"

    if normalized in ATTENTION_UNET_ALIASES:
        return "attention-unet"

    if normalized in SWIN_UNET_ALIASES:
        return "swin-unet"

    if normalized in MULTI_SENSOR_ALIASES:
        return "multi-sensor-fusion"

    return normalized or "attention-unet"


def build_model(
    model_name: str,
    *,
    in_channels: int = 4,
    out_channels: int = 3,
    base_channels: int = 32,
) -> nn.Module:
    normalized = normalize_model_name(model_name)

    if normalized == "unet-cloud-segmentation":
        return UNetCloudSegmenter(
            in_channels=max(3, in_channels),
            out_channels=1,
            base_channels=base_channels,
        )

    if normalized == "attention-unet":
        return AttentionUNetReconstructor(
            in_channels=in_channels,
            out_channels=out_channels,
            base_channels=base_channels,
        )

    if normalized == "swin-unet":
        return SwinUNetReconstructor(
            in_channels=in_channels,
            out_channels=out_channels,
            base_channels=base_channels,
        )

    if normalized == "multi-sensor-fusion":
        return MultiSensorFusionNetwork(
            liss_channels=in_channels,
            out_channels=out_channels,
            feature_channels=base_channels,
        )

    raise ValueError(f"Unknown model: {model_name}")


def checkpoint_candidates(model_name: str, model_dir: Path) -> list[Path]:
    normalized = normalize_model_name(model_name)
    return [
        model_dir / f"{normalized}.pt",
        model_dir / f"{normalized}.pth",
        model_dir / normalized / "best.pt",
        model_dir / normalized / "latest.pt",
    ]


def find_checkpoint(model_name: str, model_dir: Path) -> Path | None:
    for candidate in checkpoint_candidates(model_name, model_dir):
        if candidate.exists() and candidate.is_file():
            return candidate

    return None
