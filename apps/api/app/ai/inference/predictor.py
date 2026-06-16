from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

BASELINE_MODEL_NAMES = {
    "baseline",
    "baseline-opencv",
    "opencv",
    "opencv-baseline",
    "opencv-inpaint",
    "opencv-inpaint-telea",
}


@dataclass(frozen=True)
class AIInferencePrediction:
    reconstructed_rgb: np.ndarray
    used_model: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIInferenceAttempt:
    prediction: AIInferencePrediction | None
    fallback_reason: str | None
    metadata: dict[str, Any] = field(default_factory=dict)


def run_weighted_reconstruction_if_available(
    *,
    rgb: np.ndarray,
    invalid_mask: np.ndarray,
    requested_model: str,
    model_dir: Path,
    device: str = "cpu",
) -> AIInferenceAttempt:
    normalized_request = requested_model.strip().lower().replace("_", "-") or "opencv-baseline"
    if normalized_request in BASELINE_MODEL_NAMES:
        return AIInferenceAttempt(
            prediction=None,
            fallback_reason="baseline_requested",
            metadata={"requested_model": requested_model},
        )

    try:
        import torch

        from app.ai.models.registry import build_model, find_checkpoint, normalize_model_name
    except Exception as exc:
        return AIInferenceAttempt(
            prediction=None,
            fallback_reason="torch_unavailable",
            metadata={"error": str(exc), "requested_model": requested_model},
        )

    normalized_model = normalize_model_name(requested_model)
    checkpoint = find_checkpoint(normalized_model, model_dir)
    if checkpoint is None:
        return AIInferenceAttempt(
            prediction=None,
            fallback_reason="weights_missing",
            metadata={
                "requested_model": requested_model,
                "normalized_model": normalized_model,
                "model_dir": str(model_dir),
            },
        )

    try:
        model_input = build_reconstruction_input(rgb, invalid_mask)
        tensor = torch.from_numpy(model_input[None, ...]).float().to(device)
        model = build_model(normalized_model, in_channels=tensor.shape[1], out_channels=3)
        checkpoint_payload = torch.load(checkpoint, map_location=device)
        state_dict = checkpoint_payload.get("model_state_dict", checkpoint_payload)
        model.load_state_dict(state_dict)
        model.to(device)
        model.eval()

        with torch.no_grad():
            prediction = model(tensor)
            if prediction.shape[1] == 1:
                return AIInferenceAttempt(
                    prediction=None,
                    fallback_reason="segmentation_model_not_reconstruction",
                    metadata={"checkpoint": str(checkpoint), "normalized_model": normalized_model},
                )
            prediction = prediction.clamp(0, 1).detach().cpu().numpy()[0]

        reconstructed = (prediction.transpose(1, 2, 0) * 255).round().clip(0, 255).astype(np.uint8)
        return AIInferenceAttempt(
            prediction=AIInferencePrediction(
                reconstructed_rgb=reconstructed,
                used_model=normalized_model,
                metadata={
                    "checkpoint": str(checkpoint),
                    "device": device,
                    "model_dir": str(model_dir),
                },
            ),
            fallback_reason=None,
        )
    except Exception as exc:
        return AIInferenceAttempt(
            prediction=None,
            fallback_reason="weighted_inference_failed",
            metadata={
                "error": str(exc),
                "checkpoint": str(checkpoint),
                "normalized_model": normalized_model,
            },
        )


def build_reconstruction_input(rgb: np.ndarray, invalid_mask: np.ndarray) -> np.ndarray:
    rgb_float = rgb.astype(np.float32).transpose(2, 0, 1) / 255.0
    mask_float = (invalid_mask > 0).astype(np.float32)[None, ...]
    return np.concatenate([rgb_float, mask_float], axis=0)
