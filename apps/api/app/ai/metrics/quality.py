from __future__ import annotations

import math

import torch
from torch.nn import functional as F


def mean_absolute_error(prediction: torch.Tensor, target: torch.Tensor) -> float:
    return float((prediction - target).abs().mean().detach().cpu())


def root_mean_square_error(prediction: torch.Tensor, target: torch.Tensor) -> float:
    return float(torch.sqrt(F.mse_loss(prediction, target)).detach().cpu())


def peak_signal_noise_ratio(prediction: torch.Tensor, target: torch.Tensor) -> float:
    mse = float(F.mse_loss(prediction.clamp(0, 1), target.clamp(0, 1)).detach().cpu())
    if mse <= 1e-12:
        return 99.0

    return 20 * math.log10(1.0 / math.sqrt(mse))


def spectral_angle_mapper(
    prediction: torch.Tensor,
    target: torch.Tensor,
    eps: float = 1e-6,
) -> float:
    prediction = prediction.clamp(0, 1)
    target = target.clamp(0, 1)
    dot = (prediction * target).sum(dim=1)
    norms = prediction.norm(dim=1) * target.norm(dim=1)
    angle = torch.acos((dot / (norms + eps)).clamp(-1 + eps, 1 - eps))
    return float(angle.mean().detach().cpu())


def simple_ssim(prediction: torch.Tensor, target: torch.Tensor) -> float:
    prediction = prediction.clamp(0, 1)
    target = target.clamp(0, 1)
    c1 = 0.01**2
    c2 = 0.03**2
    mu_pred = prediction.mean(dim=(-2, -1), keepdim=True)
    mu_target = target.mean(dim=(-2, -1), keepdim=True)
    sigma_pred = ((prediction - mu_pred) ** 2).mean(dim=(-2, -1), keepdim=True)
    sigma_target = ((target - mu_target) ** 2).mean(dim=(-2, -1), keepdim=True)
    sigma_cross = ((prediction - mu_pred) * (target - mu_target)).mean(
        dim=(-2, -1),
        keepdim=True,
    )
    numerator = (2 * mu_pred * mu_target + c1) * (2 * sigma_cross + c2)
    denominator = (mu_pred.square() + mu_target.square() + c1) * (
        sigma_pred + sigma_target + c2
    )
    return float((numerator / (denominator + 1e-6)).mean().detach().cpu())


def reconstruction_metrics(prediction: torch.Tensor, target: torch.Tensor) -> dict[str, float]:
    return {
        "mae": mean_absolute_error(prediction, target),
        "rmse": root_mean_square_error(prediction, target),
        "psnr": peak_signal_noise_ratio(prediction, target),
        "sam": spectral_angle_mapper(prediction, target),
        "ssim": simple_ssim(prediction, target),
    }
